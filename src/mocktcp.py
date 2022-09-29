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
        self.transport_close_patcher = mocker.patch.object(
            self.transport, "close", self.transport_close
        )
        self.original_protocol.connection_made(transport)
        self.transport_close_patcher.start()

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
        # self.mocker = mocker
        self.service_port = service_port

        # self.open_connection_original = asyncio.open_connection
        # self.open_connection_patcher = mocker.patch(
        #     "asyncio.open_connection",
        #     self.open_connection,
        # )

        # self.create_connection_original = asyncio.get_event_loop().create_connection
        # self.create_connection_patcher = mocker.patch.object(
        #     asyncio.get_event_loop(), "create_connection",
        #     self.create_connection,
        # )
        pass

        self.task = asyncio.create_task(self.start())
        logger.info("self.task=%s", self.task)

    # async def open_connection(self, host, port):
    #     logger.info("enter: host=%s, port=%s", host, port)
    #     reader, writer = await self.open_connection_original(host, port)
    #     return reader, writer

    # async def create_connection(
    #     self, protocol_factory, host=None, port=None, *args, **kwargs
    # ):
    #     logger.info("enter: protocol_factory=%s, host=%s, port=%s", protocol_factory, host, port)
    #     protocol_interceptor = ProtocolInterceptor(
    #         self.mocker,
    #         protocol_factory()
    #     )
    #     transport, protocol = await self.create_connection_original(
    #         lambda: protocol_interceptor,
    #         host, port, *args, **kwargs
    #     )
    #     return transport, protocol

    async def stop(self):
        logger.info("entering")
        self.task.cancel()
        await self.task

    async def start(self):
        logger.info("enter: self.service_port=%s", self.service_port)
        try:
            server = await asyncio.start_server(
                self.client_handler,
                # host="localhost",
                port=self.service_port,
                start_serving=False,
            )

            # We only want one client to connect because we're mocking a service
            # to a single client not actually providing one to multiple clients.
            async with server:
                while True:
                    logger.info("loop")
                    await server.start_serving()

        except asyncio.CancelledError:
            pass

    def client_handler(self, reader, writer):
        logger.info("entering")


@pytest.fixture
async def tcpserver(mocker, unused_tcp_port):
    fixture = MockTcpServer(mocker, unused_tcp_port)
    yield fixture
    await fixture.stop()
