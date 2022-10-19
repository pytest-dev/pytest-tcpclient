import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_bytes_connection_closed(tcpserver):

    # Server expectations
    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    tcpserver.expect_bytes(b"Hello, world")
    tcpserver.expect_disconnect()

    # Client interaction
    writer.close()
    # The connection is closed before the server has a chance to read from the socket.
    await writer.wait_closed()

    await tcpserver.join()
