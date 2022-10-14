pytest-tcpclient
================

``pytest-tcpclient`` is a ``pytest`` plugin for testing TCP clients with server
mocking.

The `tcpserver` is th API to the plugin. When the `tcpserver` fixture is used a
minimal TCP server is established and will start listening on a port on the
host machine. The port number is available via the `tcpserver.service_port`
attribute. The server is running in the same process as the test case using
`asyncio`.

The `tcpserver` fixture is used to "program" the server with expectations and
to send replies to the client.

A minimal test
--------------

The simplest example of a passing test is as follows (please take note of the
comments in the code):

.. code-block:: python

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

Hello, world!
-------------

Having established a connection, we expect the client to send messages:

.. code-block:: python

    import asyncio
    import pytest


    @pytest.mark.asyncio()
    async def test_hello_world(tcpserver):

        # ==========================================================================
        # Establish expectations on server side

        tcpserver.expect_connect()
        tcpserver.expect_bytes(b"Hello, world")
        tcpserver.expect_disconnect()

        # ==========================================================================
        # Client connects, sends a message and then disconnects

        reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
        writer.write(b"Hello, world")
        writer.close()
        await writer.wait_closed()

        # ==========================================================================
        # Synchronise results

        await tcpserver.join()

