import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_disconnect_wait_closed_not_called(tcpserver):

    tcpserver.expect_connect()
    tcpserver.expect_disconnect(timeout=0.1)

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.close()

    await tcpserver.join()
