import asyncio
import pytest


@pytest.mark.asyncio()
async def test_sent_data_not_read(tcpserver):

    # Server expecations
    tcpserver.expect_connect()
    tcpserver.send_bytes(b"Hola!")
    tcpserver.expect_disconnect()

    # Client connects and disconnects but doesn't send expected message
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.close()
    await writer.wait_closed()

    # Evaluate expectations
    await tcpserver.join()
