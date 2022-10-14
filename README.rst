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

.. include:: examples/test_expect_connect.py
   :code: python

Hello, world!
-------------

Having established a connection, we expect the client to send messages:

.. include:: examples/test_hello_world.py
   :code: python

Dev Setup
---------

First initialise and activate virtual environment:

.. code-block:: sh

    $ ./scripts/init_venv
    $ source venv/bin/activate


Next, make the project:


.. code-block:: sh

    $ make
