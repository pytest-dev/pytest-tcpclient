import logging
import pytest

from mocktcp import tcpserver, MockTcpServer

import asyncio


# @pytest.mark.skip()
@pytest.mark.asyncio()
async def test_second_connection_causes_failure(tcpserver):
    assert isinstance(tcpserver, MockTcpServer)
    # logging.info("A")
    await asyncio.open_connection(None, tcpserver.service_port)
    # logging.info("B")
    with pytest.raises(Exception, match="Client is already connected"):
        # logging.info("C")
        await asyncio.open_connection(None, tcpserver.service_port)


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

    tcpserver.expect_bytes(b"Goodbye, world")
    writer.write(b"Goodbye, world")
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
