import asyncio
import pytest


@pytest.mark.asyncio()
async def test_server_disconnect(tcpserver):

    tcpserver.expect_connect()
    tcpserver.disconnect()

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    assert await reader.read() == b""

    writer.close()
    await writer.wait_closed()

    await tcpserver.join()
