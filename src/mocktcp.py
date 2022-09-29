import asyncio
import logging

import pytest


logger = logging.getLogger(__name__)


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

        logger.info("begin")
        self.transport = transport
        self.transport_close_patcher = self.mocker.patch.object(
            self.transport, "close", self.transport_close
        )
        self.original_protocol.connection_made(transport)

    def transport_close(self):
        # Stop the patch to avoid infinite recursion back to this method
        # when we call 'transport.close()' just below
        logger.info("begin")
        self.transport_close_patcher.stop()
        self.transport.close()
        logger.info("end")

    def connection_lost(self, exc):
        logger.info("begin: exc=%s", exc)
        self.original_protocol.connection_lost(exc)

    def data_received(self, data):
        logger.info("begin: data=%s", data)
        self.original_protocol.data_received(data)

    def eof_received(self):
        logger.info("begin")
        self.original_protocol.eof_received()

    # wait_closed is not part of the asyncio.Protocol interface but
    # we _do_ expect it to be on the Protocol implementations what we
    # use
    async def wait_closed(self):
        logger.info("begin")
        await self.original_protocol.wait_closed()
        self.whiteboard.wait_closed_called = True

    # Everything else just gets passed through
    def __getattr__(self, key):
        return getattr(self.original_protocol, key)


class MockTcpServer:

    def __init__(self, mocker, service_port):
        self.mocker = mocker
        self.service_port = service_port
        self.connected = False
        self.errors = []

        self.open_connection_original = asyncio.open_connection
        self.open_connection_patcher = mocker.patch(
            "asyncio.open_connection",
            self.open_connection,
        )

        self.create_connection_original = asyncio.get_event_loop().create_connection
        self.create_connection_patcher = mocker.patch.object(
            asyncio.get_event_loop(), "create_connection",
            self.create_connection,
        )

        self.task = asyncio.create_task(self.start())
        logger.info("self.task=%s", self.task)

    async def open_connection(self, host, port):
        logger.info("enter: host=%s, port=%s", host, port)
        reader, writer = await self.open_connection_original(host, port)
        self.check_for_errors()
        return reader, writer

    async def create_connection(
        self, protocol_factory, host=None, port=None, *args, **kwargs
    ):
        logger.info("enter: protocol_factory=%s, host=%s, port=%s", protocol_factory, host, port)
        protocol_interceptor = ProtocolInterceptor(
            self.mocker,
            protocol_factory()
        )
        transport, protocol = await self.create_connection_original(
            lambda: protocol_interceptor,
            host, port, *args, **kwargs
        )
        return transport, protocol

    async def stop(self):
        logger.info("entering")
        self.task.cancel()
        await self.task
        self.check_for_errors()

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
            self.errors.clear()
            raise Exception("Multiple errors")

    async def start(self):
        logger.info("enter: self.service_port=%s", self.service_port)
        try:
            server = await asyncio.start_server(
                self.client_handler,
                port=self.service_port,
                start_serving=False,
            )
            async with server:
                while not self.errors:
                    await server.start_serving()
        except asyncio.CancelledError:
            pass

    def client_handler(self, reader, writer):
        logger.info("entering")
        if self.connected:
            self.error(Exception("Client is already connected"))
        self.connected = True

    def error(self, exception):
        self.errors.append(exception)


@pytest.fixture
async def tcpserver(mocker, unused_tcp_port):
    fixture = MockTcpServer(mocker, unused_tcp_port)
    yield fixture
    await fixture.stop()
