import asyncio
import pytest

from pytest_tcpclient.framing import read_frame


@pytest.mark.asyncio()
async def test_send_frame_success(tcpserver):
    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.send_frame(b"Hello")
    assert await read_frame(reader) == b"Hello"

    writer.close()
    await writer.wait_closed()
