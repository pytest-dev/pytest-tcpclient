import asyncio
import pytest


@pytest.mark.asyncio()
async def test_sent_frame_not_read_by_client(tcpserver):
    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.send_frame(b"Hello")
    # Have to call `join` here to force `send_frame` to be executed before
    # connection is closed. If we don't do this we get a different failure message.
    await tcpserver.join()

    writer.close()
    await writer.wait_closed()

    tcpserver.expect_disconnect()
    await tcpserver.join()
