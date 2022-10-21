import asyncio
import pytest

from pytest_tcpclient.framing import write_frame


@pytest.mark.asyncio()
async def test_tcpserver_factory_two_servers_fail(tcpserver_factory):

    server_1 = await tcpserver_factory()
    server_1.expect_connect()
    server_1.expect_bytes(b"Hello_1")
    server_1.expect_disconnect()

    server_2 = await tcpserver_factory()
    server_2.expect_connect()
    server_1.expect_bytes(b"Hello_2")
    server_2.expect_disconnect()

    reader_1, writer_1 = await asyncio.open_connection(None, server_1.service_port)
    reader_2, writer_2 = await asyncio.open_connection(None, server_2.service_port)

    writer_1.write(b"Hello_2")
    writer_2.write(b"Hello_1")

    await tcpserver_factory.stop()
