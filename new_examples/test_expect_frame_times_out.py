import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_frame_times_out(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    tcpserver.expect_frame(b"Goodbye, world", timeout=0.1)

    await tcpserver.join()
