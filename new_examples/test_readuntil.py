import asyncio
import pytest


@pytest.mark.asyncio()
async def test_readuntil(tcpserver):

    # Server sends some bytes
    tcpserver.expect_connect()
    tcpserver.send_bytes(b"AAAXBBB")
    tcpserver.expect_disconnect()

    # Client only reads some of the data
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    assert await reader.readuntil(b'X') == b"AAAX"
    writer.close()
    await writer.wait_closed()

    # Evaluation
    await tcpserver.join()
