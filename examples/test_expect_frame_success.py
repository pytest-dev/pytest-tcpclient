import asyncio
import pytest
import struct


@pytest.mark.asyncio()
async def test_expect_frame_success(tcpserver):

    tcpserver.expect_connect()
    tcpserver.expect_frame(b"Goodbye, world")

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    payload = b"Goodbye, world"

    # Here's the 4-byte length header
    writer.write(struct.pack(">I", len(payload)))

    # Here's the payload
    writer.write(payload)

    # Done
    writer.close()

    await writer.wait_closed()

    await tcpserver.join()
