import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_disconnect_times_out(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.expect_connect()
    tcpserver.expect_disconnect(timeout=0.1)

    await tcpserver.join()
