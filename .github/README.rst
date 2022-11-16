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
* `Sending and receiving length-delimited "frames" <framing_>`_
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
    platform linux -- Python 3.8.10, pytest-7.2.0, pluggy-1.0.0
    rootdir: /home/anders/src/pytest-tcpclient, configfile: pyproject.toml
    plugins: mock-3.10.0, asyncio-0.20.2, cov-4.0.0, tcpclient-0.7.26.dev1+gad4c8b2.d20221115
    asyncio: mode=strict
    collected 1 item

    examples/test_hello.py .                                                 [100%]

    ============================== 1 passed in 0.03s ===============================

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
    platform linux -- Python 3.8.10, pytest-7.2.0, pluggy-1.0.0
    rootdir: /home/anders/src/pytest-tcpclient, configfile: pyproject.toml
    plugins: mock-3.10.0, asyncio-0.20.2, cov-4.0.0, tcpclient-0.7.26.dev1+gad4c8b2.d20221115
    asyncio: mode=strict
    collected 1 item

    examples/test_expect_bytes_times_out.py F                                [100%]

    =================================== FAILURES ===================================
    _________________________ test_expect_bytes_times_out __________________________

    tcpserver = <pytest_tcpclient.plugin.MockTcpServer object at 0x7fda575068b0>

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
    ============================== 1 failed in 1.04s ===============================

.. _framing:

Sending and receiving length-delimited "frames"
-----------------------------------------------

A common pattern for TCP communication is to send and receive discrete messages. One
way to represent the boundaries of these messages is to prepend a 4-byte binary
integer in network (big-endian) ordering that is the length of the payload. In
``pytest-tcpclient`` this convention is called "framing".

Here's an example of testing that a client sends a frame (``expect_frame``):

.. code-block:: python

    import asyncio
    import pytest
    import struct


    @pytest.mark.asyncio()
    async def test_expect_frame_success(tcpserver):

        tcpserver.expect_connect()
        tcpserver.expect_frame(b"Goodbye, world")

        reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

        payload = b"Goodbye, world"

        # Here's the 4-byte length header
        writer.write(struct.pack(">I", len(payload)))

        # Here's the payload
        writer.write(payload)

        # Done
        writer.close()

        await writer.wait_closed()

        await tcpserver.join()

Here's the result:

.. code-block:: python

    ============================= test session starts ==============================
    platform linux -- Python 3.8.10, pytest-7.2.0, pluggy-1.0.0
    rootdir: /home/anders/src/pytest-tcpclient, configfile: pyproject.toml
    plugins: mock-3.10.0, asyncio-0.20.2, cov-4.0.0, tcpclient-0.7.26.dev1+gad4c8b2.d20221115
    asyncio: mode=strict
    collected 1 item

    examples/test_expect_frame_success.py .                                  [100%]

    ============================== 1 passed in 0.02s ===============================

Here's an example where the server sends a frame (``send_frame``) and the client
receives it:

.. code-block:: python

    import asyncio
    import pytest
    import struct


    @pytest.mark.asyncio()
    async def test_send_frame_success(tcpserver):
        tcpserver.expect_connect()
        reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

        # The server immediately sends a frame
        tcpserver.send_frame(b"Hello")

        # The client receives the frame. First the header and then the payload.
        header_bytes = await reader.readexactly(4)
        message_length, = struct.unpack(">I", header_bytes)
        assert await reader.readexactly(message_length) == b"Hello"

        writer.close()
        await writer.wait_closed()

Here's the result:

.. code-block:: python

    ============================= test session starts ==============================
    platform linux -- Python 3.8.10, pytest-7.2.0, pluggy-1.0.0
    rootdir: /home/anders/src/pytest-tcpclient, configfile: pyproject.toml
    plugins: mock-3.10.0, asyncio-0.20.2, cov-4.0.0, tcpclient-0.7.26.dev1+gad4c8b2.d20221115
    asyncio: mode=strict
    collected 1 item

    examples/test_send_frame_success.py .                                    [100%]

    ============================== 1 passed in 0.02s ===============================

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

Build configuration is mostly stored in ``pyproject.toml``. Idealy, it would all be in
there. However, there are two exceptions.

First, ``setuptools`` has been chosen as the build system. Unfortunately, to install
``pytest-tcpclient`` in editable mode, a minimial ``setup.py`` must be and has been provided.

Packages that ``pytest-tcpclient`` requires to run are listed in ``pyproject.toml``.

Packages required for development (testing, coverage and linting) are listed in
``dev_dependencies.txt``.

``tox`` has been configured (in ``tox.ini``) to install those packages before running
the tests.

``setuptools`` has been configured to supply the option ``dev`` for those extra packages.
For example, the ``Makefile`` has the following command to initialise the virtual
environment:

.. code-block:: sh

    $ python -m pip install -e .[dev]

Default ``make`` target is ``style_and_test``
+++++++++++++++++++++++++++++++++++++++++++++

The default target in the ``Makfile`` is ``style_and_test`` which first calls
the linter, then runs the tests and, finally, checks that code coverage is 100%

``tox``
+++++++

``tox`` is only used for CI builds. See ``.github/workflows/build.yml``.

``make`` detects changes to configuration files
+++++++++++++++++++++++++++++++++++++++++++++++

If any of the build system configuration files, ``make`` will reinstall all dependencies.

Continuous Integration and Deployment
+++++++++++++++++++++++++++++++++++++

There is a workflow (``.github/workflows/build.yml``) that will build and test pull
requests with ``tox``.

There is another workflow (``.github/workflows/publish.yml``) that is triggered
by the appearance of new version tags on the ``main`` branch. It will
build and test the code and additionally publish the package to
``pypi``.

