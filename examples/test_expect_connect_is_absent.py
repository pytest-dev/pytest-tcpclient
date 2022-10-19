import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_absent_expect_connection(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")

    await tcpserver.join()
