import asyncio
import pytest


@pytest.mark.asyncio()
async def test_expect_connect_times_out(tcpserver):
    tcpserver.expect_connect(timeout=0.1)
    await tcpserver.join()
