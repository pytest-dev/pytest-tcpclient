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

Contents
--------

* `Hello <hello_>`_
* `Test Failure <test_failure_>`_
* `Development <development_>`_

.. _hello:

Hello!
------

Here's an example of a passing test that uses the ``tcpserver`` fixture:

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
    platform linux -- Python 3.8.10, pytest-7.1.2, pluggy-1.0.0
    rootdir: /home/anders/src/pytest-tcpclient, configfile: pyproject.toml
    plugins: cov-3.0.0, asyncio-0.18.3
    asyncio: mode=legacy
    collected 1 item

    examples/test_hello.py E                                                 [100%]

    ==================================== ERRORS ====================================
    _________________________ ERROR at setup of test_hello _________________________
    file /home/anders/src/pytest-tcpclient/examples/test_hello.py, line 5
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
    E       fixture 'tcpserver' not found
    >       available fixtures: LineMatcher, _config_for_test, _pytest, _sys_snapshot, cache, capfd, capfdbinary, caplog, capsys, capsysbinary, cov, doctest_namespace, event_loop, linecomp, monkeypatch, no_cover, pytestconfig, pytester, record_property, record_testsuite_property, record_xml_attribute, recwarn, testdir, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory, unused_tcp_port, unused_tcp_port_factory, unused_udp_port, unused_udp_port_factory
    >       use 'pytest --fixtures [testpath]' for help on them.

    /home/anders/src/pytest-tcpclient/examples/test_hello.py:5
    =============================== warnings summary ===============================
    ../../.local/lib/python3.8/site-packages/pytest_asyncio/plugin.py:191
      /home/anders/.local/lib/python3.8/site-packages/pytest_asyncio/plugin.py:191: DeprecationWarning: The 'asyncio_mode' default value will change to 'strict' in future, please explicitly use 'asyncio_mode=strict' or 'asyncio_mode=auto' in pytest configuration file.
        config.issue_config_time_warning(LEGACY_MODE, stacklevel=2)

    -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
    =========================== short test summary info ============================
    ERROR examples/test_hello.py::test_hello
    ========================= 1 warning, 1 error in 0.02s ==========================

.. _test_failure:

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
    platform linux -- Python 3.8.10, pytest-7.1.2, pluggy-1.0.0
    rootdir: /home/anders/src/pytest-tcpclient, configfile: pyproject.toml
    plugins: cov-3.0.0, asyncio-0.18.3
    asyncio: mode=legacy
    collected 1 item

    examples/test_expect_bytes_times_out.py E                                [100%]

    ==================================== ERRORS ====================================
    ________________ ERROR at setup of test_expect_bytes_times_out _________________
    file /home/anders/src/pytest-tcpclient/examples/test_expect_bytes_times_out.py, line 5
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
    E       fixture 'tcpserver' not found
    >       available fixtures: LineMatcher, _config_for_test, _pytest, _sys_snapshot, cache, capfd, capfdbinary, caplog, capsys, capsysbinary, cov, doctest_namespace, event_loop, linecomp, monkeypatch, no_cover, pytestconfig, pytester, record_property, record_testsuite_property, record_xml_attribute, recwarn, testdir, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory, unused_tcp_port, unused_tcp_port_factory, unused_udp_port, unused_udp_port_factory
    >       use 'pytest --fixtures [testpath]' for help on them.

    /home/anders/src/pytest-tcpclient/examples/test_expect_bytes_times_out.py:5
    =============================== warnings summary ===============================
    ../../.local/lib/python3.8/site-packages/pytest_asyncio/plugin.py:191
      /home/anders/.local/lib/python3.8/site-packages/pytest_asyncio/plugin.py:191: DeprecationWarning: The 'asyncio_mode' default value will change to 'strict' in future, please explicitly use 'asyncio_mode=strict' or 'asyncio_mode=auto' in pytest configuration file.
        config.issue_config_time_warning(LEGACY_MODE, stacklevel=2)

    -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
    =========================== short test summary info ============================
    ERROR examples/test_expect_bytes_times_out.py::test_expect_bytes_times_out
    ========================= 1 warning, 1 error in 0.02s ==========================

.. _development:

Development
-----------

If you want to use a virtual environment, do that first and activate it. You
can use any virtual environment system you like. However, if you want to use
``virtualenv`` (and you already have ``virtualenv`` installed) you could do this:

.. code-block:: sh

   $ virtualenv -p3.8 venv

Next, make the project:

.. code-block:: sh

    $ make

That will do the following:

- Install all the dependencies
- Run the tests
- Generate a coverage report
- Fail if the coverage is below 100%

Build configuration
+++++++++++++++++++

