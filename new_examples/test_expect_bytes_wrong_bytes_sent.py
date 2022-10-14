import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_bytes_wrong_bytes_sent(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.expect_bytes(b"Bonjour")
    writer.write(b"Goodbye, world")

    await tcpserver.join()
