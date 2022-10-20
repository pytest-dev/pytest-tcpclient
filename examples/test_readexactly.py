import asyncio
import pytest


@pytest.mark.asyncio()
async def test_readexactly(tcpserver):

    # Server sends some data to the client
    tcpserver.expect_connect()
    tcpserver.send_bytes(b"OneTwo")
    tcpserver.expect_disconnect()

    # Client only reads some of the sent data
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    assert await reader.readexactly(3) == b"One"
    writer.close()
    await writer.wait_closed()

    # Evaluation
    await tcpserver.join()
