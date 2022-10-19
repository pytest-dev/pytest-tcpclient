import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_disconnect_receives_unexpected_bytes(tcpserver):

    tcpserver.expect_connect()
    tcpserver.expect_disconnect(timeout=0.2)

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.write(b"Hello")
    writer.close()

    await tcpserver.join()
