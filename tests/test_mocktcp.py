import pytest

from mocktcp import tcpserver, MockTcpServer

import asyncio


@pytest.mark.asyncio()
async def test_second_connection_causes_failure(tcpserver):
    assert isinstance(tcpserver, MockTcpServer)
    await asyncio.open_connection(None, tcpserver.service_port)
    with pytest.raises(Exception, match="Client is already connected"):
        await asyncio.open_connection(None, tcpserver.service_port)
