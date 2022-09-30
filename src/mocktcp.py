import asyncio
import logging
from dataclasses import dataclass

import pytest


logger = logging.getLogger()


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
            raise Exception(f"Timed out waiting for connection")


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
                timeout=1
            )
        except asyncio.TimeoutError:
            logger.debug("Timed out")
            raise Exception(f"Timed out waiting for {self.expected_bytes}")
        if received != self.expected_bytes:
            logger.debug(f"Expected {self.expected_bytes} but got {received}")
            raise Exception(f"Expected {self.expected_bytes} but got {received}")
        logger.debug("Passed")


class SendBytes:

    def __init__(self, server, message):
        self.server = server
        self.message = message

    def __str__(self):
        return f"ExpectBytes(server={self.server}, message={self.message})"

    async def __call__(self):
        self.server.writer.write(self.message)


class MockTcpServer:

    def __init__(self, service_port):
        self.service_port = service_port
        self.connected = False
        self.errors = []
        self.stopped = False
        self.instructions = []
        self.client_connected = asyncio.Semaphore(0)
        self.expecations_queue = asyncio.Queue()

        # self.task = asyncio.create_task(self.start())
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

    def handle_client_connection(self, reader, writer):
        try:
            if self.connected:
                raise Exception("A second client connection was attempted")
            self.connected = True
            self.reader = reader
            self.writer = writer
            self.client_connected.release()
        except Exception as e:
            self.error(e)

    async def evaluate_expectations(self):
        while True:

            # If there are already errors, there's no point evaluating the expectation.
            # However, we do still have to call `task_done` on the queue to
            # signal that the expectation has been processed.

            expectation = await self.expecations_queue.get()
            if not self.errors:
                try:
                    await expectation()
                except Exception as e:
                    self.error(e)
            self.expecations_queue.task_done()

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
        await self.expecations_queue.join()
        self.check_for_errors()

    def check_not_stopped(self):
        if self.stopped:
            raise Exception("Fixture is stopped")

    def expect_connect(self, timeout=1):
        self.check_not_stopped()
        self.expecations_queue.put_nowait(ExpectConnect(self, timeout=timeout))

    def expect_bytes(self, expected_bytes):
        self.check_not_stopped()
        self.expecations_queue.put_nowait(ExpectBytes(self, expected_bytes))

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
