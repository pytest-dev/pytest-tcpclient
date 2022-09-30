import logging
import pytest

from mocktcp import tcpserver, tcpserver_factory

import asyncio


# @pytest.mark.skip()
@pytest.mark.asyncio()
async def test_second_connection_causes_failure(tcpserver):
    await asyncio.open_connection(None, tcpserver.service_port)
    await asyncio.open_connection(None, tcpserver.service_port)

    with pytest.raises(Exception, match="A second client connection was attempted"):
        await tcpserver.join()


# @pytest.mark.skip()
@pytest.mark.asyncio()
async def test_expect_connect_passes(tcpserver):
    tcpserver.expect_connect()
    await asyncio.open_connection(None, tcpserver.service_port)


# @pytest.mark.skip()
@pytest.mark.asyncio()
async def test_expect_connect_fails(tcpserver):
    tcpserver.expect_connect(timeout=0.1)
    with pytest.raises(Exception, match="Timed out waiting for connection"):
        await tcpserver.join()


# @pytest.mark.skip()
@pytest.mark.asyncio()
async def test_expect_bytes_passes(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")
    await tcpserver.join()

    # Opposite order is also okay
    writer.write(b"Goodbye, world")
    tcpserver.expect_bytes(b"Goodbye, world")
    await tcpserver.join()


# @pytest.mark.skip()
@pytest.mark.asyncio()
async def test_expect_bytes_nothing_sent_fails(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    # Passes
    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")
    await tcpserver.join()

    # Times out because nothing is sent
    tcpserver.expect_bytes(b"Hello, world")

    with pytest.raises(Exception, match="Timed out waiting for b'Hello, world'"):
        await tcpserver.join()


# @pytest.mark.skip()
@pytest.mark.asyncio()
async def test_expect_bytes_wrong_bytes_fails(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    # Passes
    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")
    await tcpserver.join()

    # Fails
    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Goodbye, world")

    with pytest.raises(Exception, match="Expected b'Hello, world' but got b'Goodbye, wor'"):
        await tcpserver.join()


# @pytest.mark.skip()
@pytest.mark.asyncio()
async def test_send_bytes(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")
    await tcpserver.join()

    tcpserver.send_bytes(b"Hola!")
    await tcpserver.join()
    assert await reader.read(5) == b"Hola!"

    tcpserver.send_bytes(b"Adios!")
    await tcpserver.join()
    assert await reader.read(6) == b"Adios!"


# @pytest.mark.skip()
@pytest.mark.asyncio()
async def test_delayed_join(tcpserver):

    # `join` not called until right at the end. This exposes a bug

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")

    tcpserver.expect_bytes(b"Goodbye, world")
    writer.write(b"Goodbye, world")
    await tcpserver.join()


@pytest.mark.xfail()
@pytest.mark.asyncio()
async def test_expect_absent_expect_connection(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")

    with pytest.raises(Exception, match="'expect_connection' has not been called"):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_early_error_doesnt_hang_test(tcpserver):

    tcpserver.expect_connect()
    tcpserver.expect_bytes(b"Hello")
    tcpserver.expect_bytes(b"Goodbye")
    tcpserver.expect_bytes(b"Sayonara")

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    # This causes the first `expect_bytes` to fail which means that the second
    # `expect_bytes` is still in the queue. This test ensures that that second
    # expectation doesn't cause `join` below to hang. It did previously.
    writer.write(b"Adios amigo!")

    with pytest.raises(Exception, match="Expected b'Hello' but got b'Adios'"):
        await tcpserver.join()


# @pytest.mark.skip()
@pytest.mark.asyncio()
async def test_tcpserver_factory_second_connection_causes_failure(tcpserver_factory):

    server_1 = await tcpserver_factory()

    await asyncio.open_connection(None, server_1.service_port)
    await asyncio.open_connection(None, server_1.service_port)

    with pytest.raises(Exception, match="A second client connection was attempted"):
        await server_1.join()

    server_2 = await tcpserver_factory()

    await asyncio.open_connection(None, server_2.service_port)
    await asyncio.open_connection(None, server_2.service_port)

    with pytest.raises(Exception, match="A second client connection was attempted"):
        await server_2.join()


# @pytest.mark.skip()
@pytest.mark.asyncio()
async def test_tcpserver_factory(tcpserver_factory):

    server_1 = await tcpserver_factory()
    server_2 = await tcpserver_factory()

    reader_1, writer_1 = await asyncio.open_connection(None, server_1.service_port)
    reader_2, writer_2 = await asyncio.open_connection(None, server_2.service_port)

    server_1.expect_connect()
    server_2.expect_connect()

    await server_1.join()
    await server_2.join()

    writer_1.write(b"Correct1")
    server_1.expect_bytes(b"Correct1")

    writer_2.write(b"Incorrect2")
    server_2.expect_bytes(b"Correct2")

    with pytest.raises(Exception, match="Expected b'Correct2' but got b'Incorrec'"):
        await server_1.join()
        await server_2.join()
