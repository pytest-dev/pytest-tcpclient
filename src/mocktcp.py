import asyncio
from dataclasses import dataclass

import pytest


class ProtocolInterceptor(asyncio.Protocol):

    def __init__(self, mocker, original_protocol):
        self.mocker = mocker
        self.original_protocol = original_protocol
        self.transport = None
        self.is_closed = False
        self.transport_close_patcher = None

    def connection_made(self, transport):
        # When a connection is made we patch the "close" method of the
        # transport to intercept calls to it

        self.transport = transport
        self.transport_close_patcher = self.mocker.patch.object(
            self.transport, "close", self.transport_close
        )
        self.original_protocol.connection_made(transport)

    def transport_close(self):
        # Stop the patch to avoid infinite recursion back to this method
        # when we call 'transport.close()' just below
        self.transport_close_patcher.stop()
        self.transport.close()

    def connection_lost(self, exc):
        self.original_protocol.connection_lost(exc)

    def data_received(self, data):
        self.original_protocol.data_received(data)

    def eof_received(self):
        self.original_protocol.eof_received()

    # # wait_closed is not part of the asyncio.Protocol interface but
    # # we _do_ expect it to be on the Protocol implementations what we
    # # use
    # async def wait_closed(self):
    #     logger.debug("begin")
    #     await self.original_protocol.wait_closed()
    #     self.whiteboard.wait_closed_called = True

    # # Everything else just gets passed through
    # def __getattr__(self, key):
    #     return getattr(self.original_protocol, key)


@dataclass
class ClientConnected:
    pass


class ExpectConnect:

    def __init__(self, server, timeout):
        self.server = server
        self.timeout = timeout

    def __str__(self):
        return "ExpectConnect()"

    async def __call__(self):
        try:
            next_event = await asyncio.wait_for(
                self.server.client_connected.acquire(),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            return f"Timed out waiting for connection"


class ExpectBytes:

    def __init__(self, server, expected_bytes):
        self.server = server
        self.expected_bytes = expected_bytes

    def __str__(self):
        return f"ExpectBytes(server={self.server}, expected_bytes={self.expected_bytes})"

    async def __call__(self):
        try:
            received = await asyncio.wait_for(
                self.server.reader.readexactly(len(self.expected_bytes)),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            return f"Timed out waiting for {self.expected_bytes}"
        if received == self.expected_bytes:
            return None
        return f"Expected {self.expected_bytes} but got {received}"


class SendBytes:

    def __init__(self, server, message):
        self.server = server
        self.message = message

    def __str__(self):
        return f"ExpectBytes(server={self.server}, message={self.message})"

    async def __call__(self):
        self.server.writer.write(self.message)


class MockTcpServer:

    def __init__(self, mocker, service_port):
        self.mocker = mocker
        self.service_port = service_port
        self.connected = False
        self.errors = []
        self.stopped = False
        self.instructions = []
        self.client_connected = asyncio.Semaphore(0)
        self.unsatisfied_expectations = asyncio.Queue()
        self.completed_expectations = asyncio.Queue()
        self.outstanding_expectation_count = 0

        self.open_connection_original = asyncio.open_connection
        mocker.patch(
            "asyncio.open_connection",
            self.open_connection,
        )

        self.create_connection_original = asyncio.get_event_loop().create_connection
        mocker.patch.object(
            asyncio.get_event_loop(), "create_connection",
            self.create_connection,
        )

        # self.task = asyncio.create_task(self.start())
        self.server = None
        self.reader = None
        self.writer = None

    async def open_connection(self, host, port):
        reader, writer = await self.open_connection_original(host, port)
        await self.join()
        return reader, writer

    async def create_connection(
        self, protocol_factory, host=None, port=None, *args, **kwargs
    ):
        protocol_interceptor = ProtocolInterceptor(
            self.mocker,
            protocol_factory()
        )
        transport, protocol = await self.create_connection_original(
            lambda: protocol_interceptor,
            host, port, *args, **kwargs
        )
        return transport, protocol

    def check_for_errors(self):
        # If we get errors, we have to clear `self.errors`.
        # If we don't do this, can `check_for_errors` has been called from somewhere
        # other than the call to `fixture.stop()` in the `tcpserver` fixture below,
        # then that call will be invoked as part of the clean up of the fixture. In that
        # case, the clean up code is being invoked _during_ the stack unwind due to
        # the exception raised below. Since `stop` invokes `check_for_errors`, it would
        # raise yet another exception if `self.errors` were not empty. There is no
        # need for that second exception because we've already raised one.
        if len(self.errors) == 1:
            error = self.errors[0]
            self.errors.clear()
            raise error
        elif len(self.errors) > 1:
            msg = ",".join(str(e) for e in self.errors)
            self.errors.clear()
            raise Exception(msg)

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client_connection,
            port=self.service_port,
            start_serving=True,
        )
        self.evaluator_task = asyncio.create_task(self.evaluate_expectations())

    def handle_client_connection(self, reader, writer):
        try:
            if self.connected:
                raise Exception("Client is already connected")
            self.connected = True
            self.reader = reader
            self.writer = writer
            self.client_connected.release()
        except Exception as e:
            self.error(e)

    async def evaluate_expectations(self):
        while not self.stopped and not self.errors:
            await self.evaluate_next_expectation()

    async def evaluate_next_expectation(self):
        expectation = await self.unsatisfied_expectations.get()
        try:
            # `expectation` returns `None` if the expectation is met, an error
            # string otherwise
            result = await expectation()
        except Exception as e:
            raise
        if result is not None:
            self.error(Exception(result))
        self.completed_expectations.put_nowait(expectation)

    def error(self, exception):
        self.errors.append(exception)

    async def stop(self):
        self.stopped = True
        try:
            await self.join()
        finally:

            self.evaluator_task.cancel()
            try:
                await self.evaluator_task
            except asyncio.CancelledError:
                pass

            self.server.close()
            await self.server.wait_closed()

    async def join(self):

        # Have to check for errors here because not all errors are caused by
        # unment expecations. Therefore, its possible for `outstanding_expectation_count` to
        # be 0 when `join` is called, which means that the body of the loop below will not
        # be executed.
        self.check_for_errors()

        # While there are still outstanding expecations, wait for each of them to
        # be completed and then check for errors.
        while self.outstanding_expectation_count:
            await self.completed_expectations.get()
            self.outstanding_expectation_count -= 1
            # May raise exception and exit loop prematurely
            self.check_for_errors()

    def check_not_stopped(self):
        if self.stopped:
            raise Exception("Fixture is stopped")

    def add_expectation(self, expectation):
        self.unsatisfied_expectations.put_nowait(expectation)
        self.outstanding_expectation_count += 1

    def expect_connect(self, timeout=5):
        self.check_not_stopped()
        self.add_expectation(ExpectConnect(self, timeout=timeout))

    def expect_bytes(self, expected_bytes):
        self.check_not_stopped()
        self.add_expectation(ExpectBytes(self, expected_bytes))

    def send_bytes(self, message):
        self.check_not_stopped()
        self.add_expectation(SendBytes(self, message))


@pytest.fixture
async def tcpserver(mocker, unused_tcp_port):
    fixture = MockTcpServer(mocker, unused_tcp_port)
    await fixture.start()
    yield fixture
    await fixture.join()
    await fixture.stop()
