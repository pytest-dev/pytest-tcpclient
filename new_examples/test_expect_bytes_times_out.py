import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_bytes_times_out(tcpserver):

    # Server expectations
    tcpserver.expect_connect()
    tcpserver.expect_bytes(b"Hello, world!", timeout=0.1)

    # Client interaction
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    # We `join` before the client closes the connection. The server will time
    # out waiting for the expected message.
    await tcpserver.join()
