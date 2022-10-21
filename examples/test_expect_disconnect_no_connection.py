import asyncio
import pytest


@pytest.mark.asyncio()
async def test_client_not_connected(tcpserver):
    tcpserver.expect_disconnect()
    await tcpserver.join()
