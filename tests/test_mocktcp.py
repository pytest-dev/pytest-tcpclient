import pytest

from mocktcp import tcpserver, MockTcpServer

import asyncio


@pytest.mark.asyncio()
async def test(tcpserver):
    assert isinstance(tcpserver, MockTcpServer)
    # await asyncio.open_connection("localhost", 1000)
    await asyncio.open_connection("localhost", tcpserver.service_port)
