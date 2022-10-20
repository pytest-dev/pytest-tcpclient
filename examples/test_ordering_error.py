import asyncio
import pytest


@pytest.mark.asyncio()
async def test_ordering_error(tcpserver):

    # This scenario used to cause an error

    tcpserver.expect_connect()
    tcpserver.expect_bytes(b"Hello")

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.write(b"Hello")

    await tcpserver.join()

    writer.close()
    await writer.wait_closed()
