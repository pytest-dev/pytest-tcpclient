import asyncio

import pytest

from pytest_tcpclient.framing import write_frame, read_frame


@pytest.mark.asyncio()
async def test_framing(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    tcpserver.expect_connect()
    await tcpserver.join()

    write_frame(writer, b"Hello")
    tcpserver.expect_bytes(b"\x00\x00\x00\x05Hello")
    tcpserver.send_bytes(b"\x00\x00\x00\x07Goodbye")

    assert await read_frame(reader) == b"Goodbye"

    writer.close()
    await writer.wait_closed()

    # After the connection is closed, `read_frame` should return an empty bytes
    assert await read_frame(reader) == b""
    assert await read_frame(reader) == b""
