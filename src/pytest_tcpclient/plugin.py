import asyncio
import logging

from dataclasses import dataclass

import pytest_asyncio


from .framing import read_frame, write_frame


logger = logging.getLogger(__name__)


@dataclass
class ServerActionEvent:
    pass


@dataclass
class ClientConnectedEvent(ServerActionEvent):
    pass


@dataclass
class ClientNotConnectedEvent(ServerActionEvent):
    pass


@dataclass
class SecondClientConnectionAttempted(ServerActionEvent):
    pass


@dataclass
class ReadZeroBytes(ServerActionEvent):
    pass


@dataclass
class ClientCalledWriterClose(ServerActionEvent):
    pass


@dataclass
class ClientCalledWriterWaitClosed(ServerActionEvent):
    pass


@dataclass
class NoRemainingSentData(ServerActionEvent):
    pass


@dataclass
class ExceptionEvent(ServerActionEvent):

    exception: Exception


@dataclass
class BytesReadEvent(ServerActionEvent):

    bytes_read: bytes


@dataclass
class FrameReadEvent(ServerActionEvent):

    payload: bytes


@dataclass
class TimeoutEvent(ServerActionEvent):
    pass


@dataclass
class IncompleteReadEvent(ServerActionEvent):

    partial: bytes


@dataclass
class UnreadSentBytes(ServerActionEvent):

    def __init__(self, unread_bytes):
        self.unread_bytes = unread_bytes


class UnexpectedEventError(Exception):

    def __init__(self, expected_event, actual_event):
        super().__init__(
            f"UnexpectedEventError(expected_event={expected_event}, actual_event={actual_event}"
        )
        self.expected_event = expected_event
        self.actual_event = actual_event

    def assertion(self):
        assert self.actual_event == self.expected_event, interpret_error(self)


class ExpectConnect:

    def __init__(self, server, timeout):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.server = server
        self.timeout = timeout

    async def server_action(self):
        # See `MockTcpServer.start` for why this method cannot itself generate
        # the `ClientConnectedEvent`
        pass

    async def evaluate(self):
        # Since `server_action` does nothing, it cannot generate an error event in the
        # case of a timeout. We have to do that here.

        try:
            self.logger.debug("Expecting connection from client")
            next_event = await asyncio.wait_for(
                self.server.server_event_queue.get(),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            self.logger.debug("Timed out waiting for client to connect")
            next_event = TimeoutEvent()

        if not isinstance(next_event, ClientConnectedEvent):
            raise UnexpectedEventError(ClientConnectedEvent(), next_event)

        self.logger.debug("Client connected")


class ExpectIsConnected:

    def __init__(self, server):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.server = server

    async def server_action(self):
        pass

    async def evaluate(self):
        # Since `server_action` does nothing, it cannot generate an error event in the
        # case of a timeout. We have to do that here.

        self.logger.debug("Expecting client to already be connected")
        if not self.server.connected:
            raise UnexpectedEventError(ClientConnectedEvent(), ClientNotConnectedEvent())

        self.logger.debug("Client connected")


class ExpectClientCalledWriterClose:

    def __init__(self, server, timeout):
        self.server = server
        self.timeout = timeout

    async def server_action(self):
        try:
            await asyncio.wait_for(
                self.server.client_called_writer_waited_closed.wait(),
                timeout=self.timeout,
            )
            return ClientCalledWriterWaitClosed()
        except asyncio.TimeoutError:
            return TimeoutEvent()

    async def evaluate(self):
        next_event = await self.server.server_event_queue.get()
        if not isinstance(next_event, ClientCalledWriterWaitClosed):
            raise UnexpectedEventError(ClientCalledWriterWaitClosed(), next_event)


class ExpectClientCalledWriterWaitClosed:

    def __init__(self, server, timeout):
        self.server = server
        self.timeout = timeout

    async def server_action(self):
        try:
            await asyncio.wait_for(
                self.server.client_called_writer_close.wait(),
                timeout=self.timeout,
            )
            return ClientCalledWriterClose()
        except asyncio.TimeoutError:
            return TimeoutEvent()

    async def evaluate(self):
        next_event = await self.server.server_event_queue.get()
        if not isinstance(next_event, ClientCalledWriterClose):
            raise UnexpectedEventError(ClientCalledWriterClose(), next_event)


class ExpectBytes:

    def __init__(self, server, expected_bytes, timeout):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.server = server
        self.expected_bytes = expected_bytes
        self.timeout = timeout

    async def server_action(self):
        try:
            self.logger.debug("Expecting to read bytes: %s", self.expected_bytes)
            received = await asyncio.wait_for(
                self.server.reader.readexactly(len(self.expected_bytes)),
                timeout=self.timeout,
            )
            self.logger.debug("Bytes read: %s", received)
            return BytesReadEvent(received)
        except asyncio.TimeoutError as e:
            self.logger.debug("Timed out waiting to read bytes %s", self.expected_bytes)
            return TimeoutEvent()
        except asyncio.IncompleteReadError as e:
            self.logger.debug(
                "Incomplete read while trying to read bytes %s", self.expected_bytes
            )
            return IncompleteReadEvent(e.partial)

    async def evaluate(self):
        next_event = await self.server.server_event_queue.get()
        if not isinstance(next_event, BytesReadEvent):
            raise UnexpectedEventError(BytesReadEvent(self.expected_bytes), next_event)
        if next_event.bytes_read != self.expected_bytes:
            raise UnexpectedEventError(BytesReadEvent(self.expected_bytes), next_event)
        self.logger.debug("Expected bytes were received: %s", self.expected_bytes)


class ExpectFrame:

    def __init__(self, server, expected_payload, timeout):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.server = server
        self.expected_payload = expected_payload
        self.timeout = timeout

    async def server_action(self):
        try:
            self.logger.debug("Expecting to read frame: %s", self.expected_payload)
            payload = await asyncio.wait_for(
                read_frame(self.server.reader),
                timeout=self.timeout,
            )
            self.logger.debug("Payload read: %s", payload)
            return FrameReadEvent(payload)
        except asyncio.TimeoutError as e:
            self.logger.debug("Timed out waiting to read frame %s", self.expected_payload)
            return TimeoutEvent()

    async def evaluate(self):
        next_event = await self.server.server_event_queue.get()
        if not isinstance(next_event, FrameReadEvent):
            raise UnexpectedEventError(FrameReadEvent(self.expected_payload), next_event)
        if next_event.payload != self.expected_payload:
            raise UnexpectedEventError(FrameReadEvent(self.expected_payload), next_event)
        self.logger.debug("Expected frame was received: %s", self.expected_payload)


class ExpectReadZeroBytes:

    def __init__(self, server, timeout):
        self.server = server
        self.timeout = timeout

    def __str__(self):
        return f"ExpectReadZeroBytes(timeout={self.timeout})"

    async def server_action(self):
        try:
            received = await asyncio.wait_for(
                self.server.reader.read(),
                timeout=self.timeout,
            )
            if len(received) == 0:
                return ReadZeroBytes()
            else:
                return BytesReadEvent(received)
        except asyncio.TimeoutError:
            return TimeoutEvent()
        except ConnectionResetError as e:
            return ReadZeroBytes()

    async def evaluate(self):
        next_event = await self.server.server_event_queue.get()
        if not isinstance(next_event, ReadZeroBytes):
            raise UnexpectedEventError(ReadZeroBytes(), next_event)


class ExpectClientReadAllSentBytes:

    def __init__(self, server, timeout):
        self.server = server
        self.timeout = timeout

    async def server_action(self):
        try:
            sent_bytes = self.server.data_sent_from_server
            read_bytes = self.server.data_read_by_client
            if read_bytes == sent_bytes:
                return NoRemainingSentData()
            else:
                assert sent_bytes.startswith(read_bytes), \
                    f"sent_bytes does not start with read_bytes: {sent_bytes=}, {read_bytes=}"
                return UnreadSentBytes(sent_bytes[len(read_bytes):])
        except asyncio.TimeoutError:
            return TimeoutEvent()

    async def evaluate(self):
        next_event = await self.server.server_event_queue.get()
        if not isinstance(next_event, NoRemainingSentData):
            raise UnexpectedEventError(NoRemainingSentData(), next_event)


class SendBytes:

    def __init__(self, server, data):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.server = server
        self.data = data

    async def server_action(self):
        self.logger.debug("Sending bytes %s", self.data)
        self.server.writer.write(self.data)
        await self.server.writer.drain()

    async def evaluate(self):
        pass


class SendFrame:

    def __init__(self, server, payload):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.server = server
        self.payload = payload

    async def server_action(self):
        self.logger.debug("Send frame %s", self.payload)
        write_frame(self.server.writer, self.payload)
        await self.server.writer.drain()

    async def evaluate(self):
        pass


class Disconnect:

    def __init__(self, server):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.server = server

    async def server_action(self):
        self.logger.debug("Server disconnecting")
        self.server.writer.close()
        await self.server.writer.wait_closed()

    async def evaluate(self):
        pass


def interpret_error(exception):

    if isinstance(exception, UnexpectedEventError):
        expected_event = exception.expected_event
        actual_event = exception.actual_event
        if isinstance(expected_event, ReadZeroBytes):
            if isinstance(actual_event, SecondClientConnectionAttempted):
                return "While waiting for client to disconnect a second connection was attempted"
            elif isinstance(actual_event, TimeoutEvent):
                return "Timed out waiting for client to disconnect. " + \
                        "Remember to call `writer.close()`."
            elif isinstance(actual_event, BytesReadEvent):
                return "Received unexpected data while waiting for client to disconnect. " + \
                        f"Data is {actual_event.bytes_read}."
            elif isinstance(actual_event, ExceptionEvent):
                if isinstance(actual_event.exception, ConnectionResetError):
                    return "Connection was reset. Did client close writer prematurely?"
        elif isinstance(expected_event, ClientConnectedEvent):
            if isinstance(actual_event, TimeoutEvent):
                return "Timed out waiting for client to connect"
            elif isinstance(actual_event, ClientNotConnectedEvent):
                return "Client is not connected. " + \
                    "Did you forget to call `asyncio.open_connection`?"
        elif isinstance(expected_event, BytesReadEvent):
            if isinstance(actual_event, TimeoutEvent):
                return f"Timed out waiting for {expected_event.bytes_read}"
            elif isinstance(actual_event, ClientConnectedEvent):
                return "Missing `expect_connect()` before " + \
                        f"`expect_bytes({expected_event.bytes_read})`"
            elif isinstance(actual_event, BytesReadEvent):
                return f"Expected to read {expected_event.bytes_read} " + \
                        f"but actually read {actual_event.bytes_read}"
            elif isinstance(actual_event, IncompleteReadEvent):
                if not actual_event.partial:
                    return f"Expected to read {expected_event.bytes_read} " + \
                            f"but only read {actual_event.partial} " + \
                            f"before the connection was closed."
        elif isinstance(expected_event, FrameReadEvent):
            if isinstance(actual_event, TimeoutEvent):
                return f"Timed out waiting for frame {expected_event.payload}"
            # elif isinstance(actual_event, ClientConnectedEvent):
            #     return "Missing `expect_connect()` before " + \
            #             f"`expect_bytes({expected_event.bytes_read})`"
            elif isinstance(actual_event, FrameReadEvent):
                return f"Expected to get frame {expected_event.payload} " + \
                        f"but actually got frame {actual_event.payload}"
        elif isinstance(expected_event, ClientCalledWriterWaitClosed):
            if isinstance(actual_event, TimeoutEvent):
                return "Timed out waiting for client to call `await writer.wait_closed()`."
        elif isinstance(expected_event, NoRemainingSentData):
            if isinstance(actual_event, UnreadSentBytes):
                return "There is data sent by server that was not read by client: " + \
                        f"unread_bytes={actual_event.unread_bytes}."
    return f"Cannot interpret {exception}, {type(exception)=}"


class InterceptorProtocol:

    def __init__(self, server, original_protocol):
        self.server = server
        self.original_protocol = original_protocol

    def connection_made(self, transport):
        self.original_protocol.connection_made(transport)

    def connection_lost(self, exc):
        self.original_protocol.connection_lost(exc)

    def pause_writing(self):
        self.original_protocol.pause_writing()

    def resume_writing(self):
        self.original_protocol.resume_writing()

    def data_received(self, data):
        self.original_protocol.data_received(data)

    def eof_received(self):
        self.original_protocol.eof_received()


class MockTcpServer:

    def __init__(self, service_port, mocker):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.service_port = service_port
        self.mocker = mocker
        self.connected = False
        self.errors = []
        self.join_already_failed = False
        self.stopped = False
        self.instructions = []
        self.server_event_queue = asyncio.Queue()
        self.server_actions = asyncio.Queue()
        self.expecations_queue = asyncio.Queue()

        self.evaluator_task = None
        self.server = None
        self.reader = None
        self.writer = None
        self.client_reader = None
        self.client_writer = None

        self.client_called_writer_close = asyncio.Event()
        self.client_called_writer_waited_closed = asyncio.Event()
        self.data_read_by_client = b""
        self.data_sent_from_server = b""

    def protocol_factory(self, original_protocol):
        return InterceptorProtocol(self, original_protocol)

    def register_client_streams(self, client_reader, client_writer):
        if self.client_reader is not None:
            return

        self.client_reader = client_reader
        self.client_writer = client_writer

        self.original_client_writer_close = self.client_writer.close
        self.mocker.patch.object(self.client_writer, "close", self.client_writer_close)

        self.original_client_writer_wait_closed = self.client_writer.wait_closed
        self.mocker.patch.object(self.client_writer, "wait_closed", self.client_writer_wait_closed)

        self.original_client_reader_read = self.client_reader.read
        self.mocker.patch.object(self.client_reader, "read", self.client_read)

        # No need to patch `readline` because it is implemented with `readuntil`
        # self.original_client_reader_readline = self.client_reader.readline
        # self.mocker.patch.object(self.client_reader, "readline", self.client_readline)

        self.original_client_reader_readexactly = self.client_reader.readexactly
        self.mocker.patch.object(self.client_reader, "readexactly", self.client_readexactly)

        self.original_client_reader_readuntil = self.client_reader.readuntil
        self.mocker.patch.object(self.client_reader, "readuntil", self.client_readuntil)

    async def client_read(self, *args, **kwargs):
        data = await self.original_client_reader_read(*args, **kwargs)
        self.data_read_by_client += data
        return data

    # async def client_readline(self, *args, **kwargs):
    #     data = await self.original_client_reader_readline(*args, **kwargs)
    #     self.data_read_by_client += data
    #     return data

    async def client_readexactly(self, *args, **kwargs):
        try:
            data = await self.original_client_reader_readexactly(*args, **kwargs)
            self.data_read_by_client += data
            return data
        except asyncio.IncompleteReadError as e:
            # Have to record the bytes we did read so that we don't wrongly accuse client
            # of not reading them.
            self.data_read_by_client += e.partial
            raise

    async def client_readuntil(self, *args, **kwargs):
        data = await self.original_client_reader_readuntil(*args, **kwargs)
        self.data_read_by_client += data
        return data

    def client_writer_close(self):
        self.client_called_writer_close.set()
        self.original_client_writer_close()

    async def client_writer_wait_closed(self):
        self.client_called_writer_waited_closed.set()
        await self.original_client_writer_wait_closed()

    async def start(self):
        self.evaluator_task = asyncio.create_task(self.evaluate_expectations())
        self.server_action_task = asyncio.create_task(self.execute_server_actions())

        # I thought it would be neater to have `ExpectConnect.server_action`
        # method call `start_accepting_connections` but then there's a race
        # between the server starting to accept connections and the test client
        # actually making the connection. If the client wins, there's no server
        # waiting on the port and connection attempt fails. I tried it and the client
        # usually wins.
        #
        # In fact, there is no guarantee that the client will call
        # `expect_connect` _before_ actually attempting the connection. It may
        # try the connection and then call `expect_connect`. We want that to
        # work. So we have to guarantee that the server is already accepting
        # connections by the time the test is invoked with the `tcpserver`
        # fixture.
        await self.start_accepting_connections()

    async def start_accepting_connections(self):

        def handle_client_connection(reader, writer):

            self.logger.debug("client connection established")
            if self.connected:
                self.server_event_queue.put_nowait(SecondClientConnectionAttempted())
                return
            self.connected = True
            self.reader = reader

            self.writer = writer

            # Capture all data sent from the server by patching `write` method of
            # the writer
            self.original_writer_write = self.writer.write
            self.mocker.patch.object(self.writer, "write", self.intercept_sent_data)

            self.server_event_queue.put_nowait(ClientConnectedEvent())

        self.server = await asyncio.start_server(
            handle_client_connection,
            port=self.service_port,
            start_serving=True,
        )

    def intercept_sent_data(self, data):
        self.data_sent_from_server += data
        self.original_writer_write(data)

    async def evaluate_expectations(self):
        while True:

            # If there are already errors, there's no point evaluating the expectation.
            # However, we do still have to call `task_done` on the queue to
            # signal that the expectation has been processed.

            expectation = await self.expecations_queue.get()
            self.logger.debug("evaluating expectation: %s", expectation)
            if not self.errors:
                # Asynchronously, we want to generate the server event that corresponds to
                # this expectation. We have to do it asynchronously because there may already
                # be other actions from previous expectations. If everything goes well, the
                # call to `evaluate` will match up with the event generated by the server
                # action.
                self.server_actions.put_nowait(expectation.server_action)
                try:
                    await expectation.evaluate()
                except Exception as e:
                    self.error(e)
            self.expecations_queue.task_done()

    async def execute_server_actions(self):
        while True:
            server_action = await self.server_actions.get()
            self.logger.debug("performing server action: %s", server_action)
            if self.errors:
                # Just drop the server action. It's irrelevant now
                continue
            try:
                server_event = await server_action()
            except Exception as e:
                # self.logger.exception("Exception during server action execution")
                server_event = ExceptionEvent(e)
            if server_event is not None:
                self.server_event_queue.put_nowait(server_event)

    def error(self, exception):
        self.errors.append(exception)

    async def stop(self):
        try:
            await self.join()
        finally:
            self.stopped = True
            # Cancel evaluator_task
            self.evaluator_task.cancel()
            try:
                await self.evaluator_task
            except asyncio.CancelledError:
                pass

            # Cancel server_action_task
            self.server_action_task.cancel()
            try:
                await self.server_action_task
            except asyncio.CancelledError:
                pass

            self.server.close()
            await self.server.wait_closed()

    async def join(self):

        if self.join_already_failed:
            return

        # Wait for all expectations to be completed, which includes failure
        await self.expecations_queue.join()

        if self.errors:
            self.join_already_failed = True
            self.errors[0].assertion()
            # raise Exception(interpret_error(self.errors[0]))

    def check_not_stopped(self):
        if self.stopped:
            raise Exception("Fixture is stopped")

    def expect_connect(self, timeout=1):
        self.check_not_stopped()
        self.expecations_queue.put_nowait(ExpectConnect(self, timeout=timeout))

    def expect_bytes(self, expected_bytes, timeout=1):
        self.check_not_stopped()
        self.expecations_queue.put_nowait(ExpectBytes(
            self, expected_bytes=expected_bytes, timeout=timeout
        ))

    def send_bytes(self, data):
        self.check_not_stopped()
        self.expecations_queue.put_nowait(SendBytes(self, data))

    def expect_frame(self, expected_payload, timeout=1):
        self.check_not_stopped()
        self.expecations_queue.put_nowait(ExpectFrame(
            self, expected_payload=expected_payload, timeout=timeout
        ))

    def send_frame(self, payload):
        self.check_not_stopped()
        self.expecations_queue.put_nowait(SendFrame(self, payload))

    def expect_disconnect(self, timeout=1):
        self.check_not_stopped()
        self.expecations_queue.put_nowait(ExpectIsConnected(self))
        self.expecations_queue.put_nowait(ExpectReadZeroBytes(self, timeout))
        self.expecations_queue.put_nowait(ExpectClientCalledWriterClose(self, timeout))
        self.expecations_queue.put_nowait(ExpectClientReadAllSentBytes(self, timeout))
        self.expecations_queue.put_nowait(ExpectClientCalledWriterWaitClosed(self, timeout))

    def disconnect(self):
        self.check_not_stopped()
        self.expecations_queue.put_nowait(Disconnect(self))


class MockTcpServerFactory:

    def __init__(self, unused_tcp_port_factory, mocker):
        self.unused_tcp_port_factory = unused_tcp_port_factory
        self.mocker = mocker
        self.servers = {}
        self.original_open_connection = asyncio.open_connection
        self.mocker.patch(
            "asyncio.open_connection",
            self.intercept_open_connection
        )
        self.orignal_create_connection = asyncio.get_event_loop().create_connection
        self.mocker.patch.object(
            asyncio.get_event_loop(),
            "create_connection",
            self.intercept_create_connection
        )

    async def __call__(self):
        server = MockTcpServer(self.unused_tcp_port_factory(), self.mocker)
        await server.start()
        self.servers[server.service_port] = server
        return server

    async def intercept_open_connection(self, host, port):
        if host is not None:
            raise Exception(
                f"`host` parameter to `open_connection` should be `None` but it is {host}"
            )
        client_reader, client_writer = await self.original_open_connection(host, port)
        server = self.servers[port]
        server.register_client_streams(client_reader, client_writer)
        return client_reader, client_writer

    async def intercept_create_connection(
        self, protocol_factory, host, port, *args, **kwargs
    ):
        server = self.servers[port]

        def factory():
            return server.protocol_factory(protocol_factory())

        return await self.orignal_create_connection(
            factory, host, port, *args, **kwargs
        )

    async def stop(self):
        errors = []
        for server in self.servers.values():
            try:
                if not server.join_already_failed:
                    server.expect_disconnect()
                await server.stop()
            except Exception as e:
                errors.append(e)
        if errors:
            raise errors[0]


@pytest_asyncio.fixture
async def tcpserver_factory(unused_tcp_port_factory, mocker):
    factory = MockTcpServerFactory(unused_tcp_port_factory, mocker)
    yield factory
    await factory.stop()


@pytest_asyncio.fixture
async def tcpserver(tcpserver_factory):
    return await tcpserver_factory()
