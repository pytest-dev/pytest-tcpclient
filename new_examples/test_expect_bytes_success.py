import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_bytes_success(tcpserver):

    # Server expectations
    tcpserver.expect_connect()
    tcpserver.expect_bytes(b"Hello, world")
    tcpserver.expect_bytes(b"Goodbye, world")

    # Client interaction
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.write(b"Hello, world")
    writer.write(b"Goodbye, world")

    writer.close()
    await writer.wait_closed()

    # Results
    await tcpserver.join()
