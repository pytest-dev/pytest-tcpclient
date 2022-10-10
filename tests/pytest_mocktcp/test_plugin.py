import asyncio
import logging
import struct

import pytest

from pytest_mocktcp.framing import write_frame, read_frame


logger = logging.getLogger(__name__)


@pytest.mark.asyncio()
async def test_expect_connect_passes_1(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.close()
    await writer.wait_closed()

    tcpserver.expect_connect()
    tcpserver.expect_disconnect()

    await tcpserver.join()

    assert await reader.read() == b""


@pytest.mark.asyncio()
async def test_expect_connect_passes_2(tcpserver):

    # Other order should also work
    tcpserver.expect_connect()
    tcpserver.expect_disconnect()

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.close()
    await writer.wait_closed()

    await tcpserver.join()


@pytest.mark.asyncio()
async def test_second_connection_causes_failure(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    tcpserver.expect_connect()

    await asyncio.open_connection(None, tcpserver.service_port)
    tcpserver.expect_disconnect()

    with pytest.raises(
        Exception,
        match="^While waiting for client to disconnect a second connection was attempted$"
    ):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_expect_connect_fails(tcpserver):
    tcpserver.expect_connect(timeout=0.1)
    with pytest.raises(Exception, match="^Timed out waiting for client to connect$"):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_expect_disconnect_times_out(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.expect_connect()
    tcpserver.expect_disconnect(timeout=0.1)

    with pytest.raises(
        Exception,
        match=r"^Timed out waiting for client to disconnect. Remember to call `writer.close\(\)`.$"
    ):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_expect_disconnect_receives_unexpected_bytes(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.write(b"Hello")
    writer.close()

    tcpserver.expect_connect()
    tcpserver.expect_disconnect(timeout=0.2)

    with pytest.raises(
        Exception,
        match=r"^Received unexpected data while waiting for client to disconnect. "
            "Data is b'Hello'.$"
    ):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_expect_bytes_passes(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    # Expectation followed by client action should work
    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")

    # Client action followed by expectation should also work
    writer.write(b"Goodbye, world")
    tcpserver.expect_bytes(b"Goodbye, world")
    await tcpserver.join()

    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio()
async def test_expect_bytes_nothing_sent_fails(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    # Passes
    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")
    await tcpserver.join()

    # Times out because nothing is sent
    tcpserver.expect_bytes(b"Goodbye, world", timeout=0.1)

    with pytest.raises(Exception, match=r"^Timed out waiting for b'Goodbye, world'$"):
        await tcpserver.join()

    writer.close()


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
    tcpserver.expect_bytes(b"Bonjour")
    writer.write(b"Goodbye, world")

    with pytest.raises(
        Exception,
        match="^Expected to read b'Bonjour' but actually read b'Goodbye'$"
    ):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_send_bytes(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    tcpserver.send_bytes(b"Hola!")
    await tcpserver.join()
    assert await reader.read(5) == b"Hola!"

    tcpserver.send_bytes(b"Adios!")
    await tcpserver.join()
    assert await reader.read(6) == b"Adios!"

    writer.close()
    assert await reader.read() == b""

    await writer.wait_closed()


@pytest.mark.asyncio()
async def test_no_remaining_sent_data(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    tcpserver.send_bytes(b"Hola!")
    await tcpserver.join()
    assert await reader.read(5) == b"Hola!"

    tcpserver.send_bytes(b"Adios!")

    writer.close()
    await writer.wait_closed()

    tcpserver.expect_disconnect()

    with pytest.raises(
        Exception,
        match=r"^There is data sent by server that was not read by client: unread_bytes=b'Adios!'.$"
    ):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_readline(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    tcpserver.send_bytes(b"One\nTwo\n")
    await tcpserver.join()
    assert await reader.readline() == b"One\n"

    writer.close()
    await writer.wait_closed()

    tcpserver.expect_disconnect()

    with pytest.raises(
        Exception,
        match=r"^There is data sent by server that was not read by client: unread_bytes=b'Two\\n'."
    ):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_readexactly(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    tcpserver.send_bytes(b"OneTwo")
    await tcpserver.join()
    assert await reader.readexactly(3) == b"One"

    writer.close()
    await writer.wait_closed()

    tcpserver.expect_disconnect()

    with pytest.raises(
        Exception,
        match=r"^There is data sent by server that was not read by client: unread_bytes=b'Two'."
    ):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_readuntil(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    tcpserver.send_bytes(b"AAAXBBB")
    await tcpserver.join()
    assert await reader.readuntil(b'X') == b"AAAX"

    writer.close()
    await writer.wait_closed()

    tcpserver.expect_disconnect()

    with pytest.raises(
        Exception,
        match=r"^There is data sent by server that was not read by client: unread_bytes=b'BBB'."
    ):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_connection_reset_error(tcpserver):

    # Somehow, the following scenario causes a connection reset error to be raised in the
    # mock server. Probably it will run differently on platforms other than Python 3.8 on Linux.

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    await tcpserver.join()

    tcpserver.send_bytes(b"Hola!")
    await tcpserver.join()
    assert await reader.read(5) == b"Hola!"

    tcpserver.send_bytes(b"Adios!")
    tcpserver.send_bytes(b"Amigo!")

    writer.close()
    await writer.wait_closed()

    tcpserver.expect_disconnect()

    with pytest.raises(
        Exception,
        match=r"^Connection was reset. Did client close writer prematurely\?$"
    ):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_delayed_join(tcpserver):

    # `join` not called until right at the end. This was written to expose a bug that
    # is now fixed.

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")

    tcpserver.expect_bytes(b"Goodbye, world")
    writer.write(b"Goodbye, world")
    await tcpserver.join()

    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio()
async def test_expect_absent_expect_connection(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")

    with pytest.raises(
        Exception, match=r"^Missing `expect_connect\(\)` before `expect_bytes\(b'Hello, world'\)`$"
    ):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_early_error_doesnt_hang_test(tcpserver):

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.expect_connect()
    tcpserver.expect_bytes(b"Hello")
    tcpserver.expect_bytes(b"Goodbye")
    tcpserver.expect_bytes(b"Sayonara")

    # This causes the first `expect_bytes` to fail which means that the second
    # `expect_bytes` is still in the expectation queue. This test ensures that that second
    # expectation doesn't cause `join` below to hang. It did previously.
    writer.write(b"Adios amigo!")

    with pytest.raises(Exception, match="^Expected to read b'Hello' but actually read b'Adios'$"):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_ordering_error(tcpserver):

    # This scenario used to cause an error

    tcpserver.expect_connect()
    tcpserver.expect_bytes(b"Hello")

    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    writer.write(b"Hello")

    await tcpserver.join()

    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio()
async def test_expect_frame_passes(tcpserver):
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)
    tcpserver.expect_connect()

    writer.write(b"Hello, world")
    tcpserver.expect_bytes(b"Hello, world")

    write_frame(writer, b"Goodbye, world")
    tcpserver.expect_frame(b"Goodbye, world")

    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio()
async def test_expect_frame_nothing_sent_fails(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    # Passes
    writer.write(b"Hello, world")
    tcpserver.expect_bytes(b"Hello, world")
    await tcpserver.join()

    # Times out because nothing is sent
    tcpserver.expect_frame(b"Goodbye, world", timeout=0.1)

    with pytest.raises(Exception, match=r"^Timed out waiting for frame b'Goodbye, world'$"):
        await tcpserver.join()

    writer.close()


@pytest.mark.asyncio()
async def test_expect_frame_wrong_bytes_fails(tcpserver):

    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    # Passes
    tcpserver.expect_bytes(b"Hello, world")
    writer.write(b"Hello, world")
    await tcpserver.join()

    # Times out because nothing is sent
    tcpserver.expect_frame(b"Bonjour")
    write_frame(writer, b"Goodbye, world")

    with pytest.raises(
        Exception,
        match=r"^Expected to get frame b'Bonjour' but actually got frame b'Goodbye, world'$"
    ):
        await tcpserver.join()

    writer.close()


@pytest.mark.asyncio()
async def test_send_frame(tcpserver):
    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.send_frame(b"Hello")
    assert await read_frame(reader) == b"Hello"

    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio()
async def test_sent_frame_not_read_by_client(tcpserver):
    tcpserver.expect_connect()
    reader, writer = await asyncio.open_connection(None, tcpserver.service_port)

    tcpserver.send_frame(b"Hello")
    await tcpserver.join()

    writer.close()
    await writer.wait_closed()
    tcpserver.expect_disconnect()

    with pytest.raises(
        Exception,
        match=r"^There is data sent by server that was not read by client: "
            r"unread_bytes=b'\\x00\\x00\\x00\\x05Hello"
    ):
        await tcpserver.join()


@pytest.mark.asyncio()
async def test_tcpserver_factory_second_connection_causes_failure(tcpserver_factory):

    server_1 = await tcpserver_factory()

    await asyncio.open_connection(None, server_1.service_port)
    await asyncio.open_connection(None, server_1.service_port)

    server_1.expect_connect()
    server_1.expect_disconnect()

    with pytest.raises(
        Exception,
        match="^While waiting for client to disconnect a second connection was attempted$"
    ):
        await server_1.join()

    server_2 = await tcpserver_factory()

    await asyncio.open_connection(None, server_2.service_port)
    await asyncio.open_connection(None, server_2.service_port)

    server_2.expect_connect()
    server_2.expect_disconnect()

    with pytest.raises(
        Exception,
        match="^While waiting for client to disconnect a second connection was attempted$"
    ):
        await server_2.join()


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

    with pytest.raises(
        Exception, match="^Expected to read b'Correct2' but actually read b'Incorrec'$"
    ):
        await server_1.join()
        await server_2.join()

    assert server_2.join_already_failed

    server_1.expect_disconnect(timeout=0.1)
    with pytest.raises(
        Exception,
        match=r"^Timed out waiting for client to disconnect. Remember to call `writer.close\(\)`.$"
    ):
        await server_1.join()
