import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_connect_passes_1(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.close()
    await writer.wait_closed()

    tcpserver.expect_connect()
    tcpserver.expect_disconnect()

    await tcpserver.join()

    assert await reader.read() == b""
