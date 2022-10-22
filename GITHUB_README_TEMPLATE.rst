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

.. include:: examples/test_hello.py
    :code: python

Here's the result:

.. include:: examples_output/test_hello.txt
    :code: python

Test Failure
------------

This example demonstrates test failure.

It is similar to the previous example except that the client does not send the
expected message. As a result, the server times out while waiting for that
message and the test fails.

.. include:: examples/test_expect_bytes_times_out.py
    :code: python

Here's the result:
.. include:: examples_output/test_expect_bytes_times_out.txt
    :code: python