import asyncio
import pytest


@pytest.mark.asyncio()
async def test_tcpserver_factory_second_connection_causes_failure(tcpserver_factory):

    server = await tcpserver_factory()
    server.expect_connect()
    server.expect_disconnect()

    reader, writer = await asyncio.open_connection(None, server.service_port)
    reader, writer = await asyncio.open_connection(None, server.service_port)

    writer.close()
    await writer.wait_closed()
    await server.join()
