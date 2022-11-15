import asyncio
import pytest
import struct


@pytest.mark.asyncio()
async def test_send_frame_success(tcpserver):
    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    # The server immediately sends a frame
    tcpserver.send_frame(b"Hello")

    # The client receives the frame. First the header and then the payload.
    header_bytes = await reader.readexactly(4)
    message_length, = struct.unpack(">I", header_bytes)
    assert await reader.readexactly(message_length) == b"Hello"

    writer.close()
    await writer.wait_closed()
