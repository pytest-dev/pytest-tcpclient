pytest-tcpclient
================


``pytest-tcpclient`` is a ``pytest`` plugin that helps you write better TCP clients.

It provides two fixtures, ``tcpserver`` and ``tcpserver_factory``.

Behind the scenes, the ``tcpserver`` fixture creates an in-process TCP server
that listens on a port to which the client can connect and send messages and
from which it can receive replies.

The ``tcpserver`` fixture is used to express expectations about what messages the
client sends and also to send replies to it. If any expectation is unfulfilled, the
test will fail with a diagnostic message.

Hello!
------

Here's an example of a passing test that uses the `tcpserver` fixture:

.. code-block:: python

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

Here's the result:

.. code-block:: python

    ============================= test session starts ==============================
    platform linux -- Python 3.8.10, pytest-7.1.3, pluggy-1.0.0
    rootdir: /home/anders/src/pytest-tcpclient, configfile: pyproject.toml
    plugins: mock-3.10.0, asyncio-0.19.0, cov-4.0.0, tcpclient-0.7.14
    asyncio: mode=strict
    collected 1 item

    examples/test_hello.py .                                                 [100%]

    ============================== 1 passed in 0.02s ===============================

Test Failure
------------

This example demonstrates test failure.

It is similar to the previous example except that the client does not send the
expected message. As a result, the server times out while waiting for that
message and the test fails.

.. code-block:: python

    import asyncio
    import pytest


    @pytest.mark.asyncio()
    async def test_expect_bytes_times_out(tcpserver):

        # --------------------------------------------------------------------------
        # Server expectations. The server just expects the client to connect, send
        # a message and then disconnect.

        tcpserver.expect_connect()
        tcpserver.expect_bytes(b"Hello, world!")
        tcpserver.expect_disconnect()

        # --------------------------------------------------------------------------
        # The client connects but it does not send the message and it does not close
        # the connection.

        reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

        # --------------------------------------------------------------------------
        # The server will time out waiting for the expected message. The test will
        # fail with a diagnostic message.

        await tcpserver.join()

Here's the result:

.. code-block:: python

    ============================= test session starts ==============================
    platform linux -- Python 3.8.10, pytest-7.1.3, pluggy-1.0.0
    rootdir: /home/anders/src/pytest-tcpclient, configfile: pyproject.toml
    plugins: mock-3.10.0, asyncio-0.19.0, cov-4.0.0, tcpclient-0.7.14
    asyncio: mode=strict
    collected 1 item

    examples/test_expect_bytes_times_out.py F                                [100%]

    =================================== FAILURES ===================================
    _________________________ test_expect_bytes_times_out __________________________

    tcpserver = <pytest_tcpclient.plugin.MockTcpServer object at 0x7f3ee4810b80>

        @pytest.mark.asyncio()
        async def test_expect_bytes_times_out(tcpserver):

            # --------------------------------------------------------------------------
            # Server expectations. The server just expects the client to connect, send
            # a message and then disconnect.

            tcpserver.expect_connect()
            tcpserver.expect_bytes(b"Hello, world!")
            tcpserver.expect_disconnect()

            # --------------------------------------------------------------------------
            # The client connects but it does not send the message and it does not close
            # the connection.

            reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

            # --------------------------------------------------------------------------
            # The server will time out waiting for the expected message. The test will
            # fail with a diagnostic message.

    >       await tcpserver.join()
    E       Failed: Timed out waiting for b'Hello, world!'

    examples/test_expect_bytes_times_out.py:26: Failed
    =========================== short test summary info ============================
    FAILED examples/test_expect_bytes_times_out.py::test_expect_bytes_times_out
    ============================== 1 failed in 1.06s ===============================

