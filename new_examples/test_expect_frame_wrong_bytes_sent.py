import asyncio
import pytest

from pytest_tcpclient.framing import write_frame


@pytest.mark.asyncio()
async def test_expect_frame_wrong_bytes_sent(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.expect_frame(b"Bonjour")
    write_frame(writer, b"Goodbye, world")

    await tcpserver.join()
