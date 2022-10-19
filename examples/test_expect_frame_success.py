import asyncio
import pytest

from pytest_tcpclient.framing import write_frame


@pytest.mark.asyncio()
async def test_expect_frame_success(tcpserver):

    tcpserver.expect_connect()
    tcpserver.expect_bytes(b"Hello, world")
    tcpserver.expect_frame(b"Goodbye, world")

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.write(b"Hello, world")
    write_frame(writer, b"Goodbye, world")
    writer.close()
    await writer.wait_closed()

    await tcpserver.join()
