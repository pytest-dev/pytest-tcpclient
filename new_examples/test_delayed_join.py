import asyncio
import pytest


@pytest.mark.asyncio()
async def test_delayed_join(tcpserver):

    # `join` not called until right at the end. This was written to expose a bug that
    # is now fixed.

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")

    tcpserver.expect_bytes(b"Goodbye, world")
    writer.write(b"Goodbye, world")
    await tcpserver.join()

    writer.close()
    await writer.wait_closed()
