import asyncio
import pytest


@pytest.mark.asyncio()
async def test_hello_world(tcpserver):

    # ==========================================================================
    # Establish expectations on server side

    tcpserver.expect_connect()
    tcpserver.expect_bytes(b"Hello, world")
    tcpserver.expect_disconnect()

    # ==========================================================================
    # Client connects, sends a message and then disconnects

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.write(b"Hello, world")
    writer.close()
    await writer.wait_closed()

    # ==========================================================================
    # Synchronise results

    await tcpserver.join()
