import asyncio
from dataclasses import dataclass

import pytest


@dataclass
class ClientConnectedEvent:
    pass


@dataclass
class ErrorEvent:

    exception: Exception


@dataclass
class BytesReadEvent:

    bytes_read: bytes


class ExpectConnect:

    def __init__(self, server, timeout):
        self.server = server
        self.timeout = timeout

    def __str__(self):
        return "ExpectConnect()"

    async def server_action(self):
        # The server already has code to perform client connection and generate
        # `ClientConnectedEvent`
        pass

    async def evaluate(self):
        try:
            next_event = await asyncio.wait_for(
                self.server.actual_events_queue.get(),
                timeout=self.timeout,
            )
            if not isinstance(next_event, ClientConnectedEvent):
                raise Exception(f"Expected connect event but got {next_event}")
        except asyncio.TimeoutError:
            raise Exception(f"Timed out waiting for connection")


class ExpectBytes:

    def __init__(self, server, expected_bytes, timeout):
        self.server = server
        self.expected_bytes = expected_bytes
        self.timeout = timeout

    def __str__(self):
        return f"ExpectBytes(expected_bytes={self.expected_bytes})"

    async def server_action(self):
        try:
            received = await asyncio.wait_for(
                self.server.reader.readexactly(len(self.expected_bytes)),
                timeout=1,
            )
            return BytesReadEvent(received)
        except asyncio.TimeoutError:
            raise Exception(f"Timed out waiting for {self.expected_bytes}")

    async def evaluate(self):
        try:
            next_event = await asyncio.wait_for(
                self.server.actual_events_queue.get(),
                timeout=self.timeout,
            )
            if not isinstance(next_event, BytesReadEvent):
                raise Exception(f"Expected BytesReadEvent event but got {next_event}")
            if next_event.bytes_read != self.expected_bytes:
                raise Exception(f"Expected {self.expected_bytes} but got {next_event.bytes_read}")
        except asyncio.TimeoutError:
            raise Exception(f"Timed out waiting for {self.expected_bytes}")


class SendBytes:

    def __init__(self, server, message):
        self.server = server
        self.message = message

    def __str__(self):
        return f"SendBytes(message={self.message})"

    async def server_action(self):
        self.server.writer.write(self.message)

    async def evaluate(self):
        pass


class MockTcpServer:

    def __init__(self, service_port):
        self.service_port = service_port
        self.connected = False
        self.errors = []
        self.stopped = False
        self.instructions = []
        self.actual_events_queue = asyncio.Queue()
        self.server_actions = asyncio.Queue()
        self.expecations_queue = asyncio.Queue()

        self.evaluator_task = None
        self.server = None
        self.reader = None
        self.writer = None

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
        self.server_action_task = asyncio.create_task(self.execute_server_actions())

    def handle_client_connection(self, reader, writer):
        try:
            if self.connected:
                raise Exception("A second client connection was attempted")
            self.connected = True
            self.reader = reader
            self.writer = writer
            self.actual_events_queue.put_nowait(ClientConnectedEvent())
        except Exception as e:
            self.error(e)

    async def evaluate_expectations(self):
        while True:

            # If there are already errors, there's no point evaluating the expectation.
            # However, we do still have to call `task_done` on the queue to
            # signal that the expectation has been processed.

            expectation = await self.expecations_queue.get()
            if not self.errors:
                self.server_actions.put_nowait(expectation.server_action)
                try:
                    await expectation.evaluate()
                except Exception as e:
                    self.error(e)
            self.expecations_queue.task_done()

    async def execute_server_actions(self):
        while True:
            server_action = await self.server_actions.get()
            try:
                event = await server_action()
            except Exception as e:
                event = ErrorEvent(e)
            if event is not None:
                self.actual_events_queue.put_nowait(event)

    def error(self, exception):
        self.errors.append(exception)

    async def stop(self):
        self.stopped = True
        try:
            await self.join()
        finally:

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
        await self.expecations_queue.join()
        self.check_for_errors()

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

    def send_bytes(self, message):
        self.check_not_stopped()
        self.expecations_queue.put_nowait(SendBytes(self, message))


@pytest.fixture
async def tcpserver(unused_tcp_port):
    server = MockTcpServer(unused_tcp_port)
    await server.start()
    yield server
    await server.stop()



class MockTcpServerFactory:

    def __init__(self, unused_tcp_port_factory):
        self.unused_tcp_port_factory = unused_tcp_port_factory
        self.servers = []

    async def __call__(self):
        server = MockTcpServer(self.unused_tcp_port_factory())
        await server.start()
        self.servers.append(server)
        return server

    async def stop(self):
        for server in self.servers:
            try:
                await server.stop()
            except Exception as e:
                errors.append(e)


@pytest.fixture
async def tcpserver_factory(unused_tcp_port_factory):
    factory = MockTcpServerFactory(unused_tcp_port_factory)
    yield factory
    await factory.stop()
