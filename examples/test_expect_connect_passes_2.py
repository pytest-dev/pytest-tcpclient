import pytest
import asyncio


@pytest.mark.asyncio()
async def test_expect_connect_passes_2(tcpserver):

    # Other order should also work
    tcpserver.expect_connect()
    tcpserver.expect_disconnect()

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.close()
    await writer.wait_closed()

    await tcpserver.join()
