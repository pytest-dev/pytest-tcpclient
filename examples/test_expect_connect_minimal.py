import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_connect_minimal(tcpserver):

    tcpserver.expect_connect()

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.close()
    await writer.wait_closed()
