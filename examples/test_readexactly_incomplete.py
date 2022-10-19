import asyncio
import pytest


@pytest.mark.asyncio()
async def test_readexactly_incomplete(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    tcpserver.expect_connect()

    tcpserver.send_bytes(b"\x00")
    tcpserver.disconnect()

    # This was causing an test error because the one byte that was read was not
    # being captured. As a result, the error wrongly claimed that the client
    # had failed to read that byte.

    with pytest.raises(asyncio.IncompleteReadError):
        assert await reader.readexactly(2)

    writer.close()
    await writer.wait_closed()

    await tcpserver.join()
