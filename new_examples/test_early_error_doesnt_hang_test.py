import asyncio
import pytest


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

    await tcpserver.join()
