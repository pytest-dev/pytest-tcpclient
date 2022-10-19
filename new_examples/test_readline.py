import asyncio
import pytest


@pytest.mark.asyncio()
async def test_readline(tcpserver):

    # Server expectations
    tcpserver.expect_connect()
    tcpserver.send_bytes(b"One\nTwo\n")
    tcpserver.expect_disconnect()

    # Client reads the first line but not the second. The test will fail
    # and the unread bytes will be reported.
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    assert await reader.readline() == b"One\n"
    writer.close()
    await writer.wait_closed()

    # Evaluate
    await tcpserver.join()
