import pytest
import asyncio


@pytest.mark.asyncio()
async def test_exception_in_test(tcpserver):

    tcpserver.expect_connect()
    tcpserver.expect_disconnect()

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    raise Exception("Exception")

    await tcpserver.join()
