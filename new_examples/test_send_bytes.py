import asyncio
import pytest


@pytest.mark.asyncio()
async def test_send_bytes(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    tcpserver.send_bytes(b"Hola!")
    await tcpserver.join()
    assert await reader.read(5) == b"Hola!"

    tcpserver.send_bytes(b"Adios!")
    await tcpserver.join()
    assert await reader.read(6) == b"Adios!"

    writer.close()
    assert await reader.read() == b""

    await writer.wait_closed()
