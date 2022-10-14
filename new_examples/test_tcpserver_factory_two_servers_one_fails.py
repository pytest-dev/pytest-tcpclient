import asyncio
import pytest

from pytest_tcpclient.framing import write_frame


@pytest.mark.asyncio()
async def test_tcpserver_factory_two_servers_one_fails(tcpserver_factory):

    server_1 = await tcpserver_factory()
    server_1.expect_connect()
    server_1.expect_frame(b"Client hello 1")
    server_1.expect_disconnect()

    server_2 = await tcpserver_factory()
    server_2.expect_connect()
    server_2.expect_frame(b"Client hello 2")
    server_2.expect_disconnect()

    reader_1, writer_1 = await asyncio.open_connection(None, server_1.service_port)
    write_frame(writer_1, b"Client hello 1")
    writer_1.close()
    await writer_1.wait_closed()

    reader_2, writer_2 = await asyncio.open_connection(None, server_2.service_port)
    # Doesn't send expected frame
    writer_2.close()
    await writer_2.wait_closed()

    await server_1.join()
    await server_2.join()
