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

.. include:: examples/test_hello.py
    :code: python

Here's the result:

.. include:: examples_output/test_hello.txt
    :code: python


.. _test_failure:

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

.. _framing:

Sending and receiving length-delimited "frames"
-----------------------------------------------

A common pattern for TCP communication is to send and receive discrete messages. One
way to represent the boundaries of these messages is to prepend a 4-byte binary
integer in network (big-endian) ordering that is the length of the payload. In
``pytest-tcpclient`` this convention is called "framing".

Here's an example of testing that a client sends a frame (``expect_frame``):

.. include:: examples/test_expect_frame_success.py
    :code: python

Here's the result:

.. include:: examples_output/test_expect_frame_success.txt
    :code: python

Here's an example where the server sends a frame (``send_frame``) and the client
receives it:

.. include:: examples/test_send_frame_success.py
    :code: python

Here's the result:

.. include:: examples_output/test_send_frame_success.txt
    :code: python

.. _development:

.. include:: DEV_README.rst
