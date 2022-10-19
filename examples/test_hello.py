import asyncio
import pytest


@pytest.mark.asyncio()
async def test_hello(tcpserver):

    # ==========================================================================
    # Establish expectations and replies on the server side.
    #
    # In this case, the client is expected to connect and then send a specific
    # message. If that occurs, the server will send a reply. It is expected
    # that the client will then disconnect.

    tcpserver.expect_connect()
    tcpserver.expect_bytes(b"Hello, server!")
    tcpserver.send_bytes(b"Hello, client!")
    tcpserver.expect_disconnect()

    # ==========================================================================
    # Client interacts with server.
    #
    # It connects, sends the expected message and then receives the reply.
    # Finally, it disconnects from the server.

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    writer.write(b"Hello, server!")
    assert await reader.readexactly(14) == b"Hello, client!"

    writer.close()
    await writer.wait_closed()

    # ==========================================================================
    # Synchronise with server. Test failures, if any, will be reported here. In
    # this case, there are no failures.

    await tcpserver.join()
