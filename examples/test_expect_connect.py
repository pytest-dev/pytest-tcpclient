import asyncio
import pytest

@pytest.mark.asyncio()
async def test_expect_connect(tcpserver):

    # When we enter the test, the test server is already running and waiting
    # for a connection from the client. It is running in an `asyncio.Task`.
    #
    # It is listening on port `tcpserver.service_port` on the local machine

    # ==========================================================================
    # Initially, we tell the server what we're expecting the client to do. In
    # this case, we expect the client to connect and then to immediately
    # disconnect.

    tcpserver.expect_connect()
    tcpserver.expect_disconnect()

    # In all tests, the first expectation must be `expect_connect`. An error
    # will be raised if this is not the case. The final one should be
    # `expect_disconnect`.
    #
    # Behind the scenes, the server will record the _actual_ interactions with
    # the client and compare them to the expectations. It records the
    # outcomes of those comparisons asynchronously. When `tcpserver.join` is
    # called (below), errors will be raised if they occurred.

    # ==========================================================================
    # Having specifiied the expectations, the client now interacts with
    # the server.

    # This is the connection expected by the server. Note that `host` is `None.
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    # Here's the disconnection expected by the server. Both `close` and `wait_closed`
    # are required to complete the disconnection.
    writer.close()
    await writer.wait_closed()

    # =========================================================================
    # Finally, `join` with the server. If there is an unfulfilled expectation or
    # some other error, this function will raise an exception.

    await tcpserver.join()
