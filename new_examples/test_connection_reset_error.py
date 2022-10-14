import asyncio
import pytest


@pytest.mark.asyncio()
async def test_connection_reset_error(tcpserver):

    # Somehow, the following scenario causes a connection reset error to be raised in the
    # mock server. Probably it will run differently on platforms other than Python 3.8 on Linux.

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    tcpserver.send_bytes(b"Hola!")
    await tcpserver.join()
    assert await reader.read(5) == b"Hola!"

    tcpserver.send_bytes(b"Adios!")
    tcpserver.send_bytes(b"Amigo!")

    writer.close()
    await writer.wait_closed()

    tcpserver.expect_disconnect()

    await tcpserver.join()
