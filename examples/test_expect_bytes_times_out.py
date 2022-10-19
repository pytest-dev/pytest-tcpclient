import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_bytes_times_out(tcpserver):

    # --------------------------------------------------------------------------
    # Server expectations. The server just expects the client to connect, send
    # a message and then disconnect.

    tcpserver.expect_connect()
    tcpserver.expect_bytes(b"Hello, world!")
    tcpserver.expect_disconnect()

    # --------------------------------------------------------------------------
    # The client connects but it does not send the message and it does not close
    # the connection.

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    # --------------------------------------------------------------------------
    # The server will time out waiting for the expected message. The test will
    # fail with a diagnostic message.

    await tcpserver.join()
