import asyncio
import pytest


@pytest.mark.asyncio()
async def test_second_connection_causes_failure(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    tcpserver.expect_connect()

    await asyncio.open_connection(None, tcpserver.service_port)
    tcpserver.expect_disconnect()

    await tcpserver.join()
