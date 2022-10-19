import asyncio
import pytest


def assert_failure(result, message, server_variable_name="tcpserver"):
    __tracebackhide__ = True
    result.assert_outcomes(failed=1)
    lines = result.stdout.get_lines_after(f">       await {server_variable_name}.join()")
    assert lines[0] == f"E       Failed: {message}"


def test_expect_connect_passes_1(pytester):
    pytester.copy_example("test_expect_connect_passes_1.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_expect_connect_passes_2(pytester):
    pytester.copy_example("test_expect_connect_passes_2.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_expect_connect_minimal(pytester):
    pytester.copy_example("test_expect_connect_minimal.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_second_connection_causes_failure(pytester):
    pytester.copy_example("test_second_connection_causes_failure.py")
    result = pytester.runpytest()
    assert_failure(
        result, "While waiting for client to disconnect a second connection was attempted."
    )


def test_expect_connect_times_out(pytester):
    pytester.copy_example("test_expect_connect_times_out.py")
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    assert_failure(result, "Timed out waiting for client to connect.")


def test_expect_disconnect_times_out(pytester):
    pytester.copy_example("test_expect_disconnect_times_out.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "Timed out waiting for client to disconnect. Remember to call `writer.close()`."
    )


def test_expect_disconnect_receives_unexpected_bytes(pytester):
    pytester.copy_example("test_expect_disconnect_receives_unexpected_bytes.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "Received unexpected data while waiting for client to disconnect. Data is b'Hello'."
    )


def test_expect_bytes_success(pytester):
    pytester.copy_example("test_expect_bytes_success.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_expect_bytes_times_out(pytester):
    pytester.copy_example("test_expect_bytes_times_out.py")
    result = pytester.runpytest()
    assert_failure(result, "Timed out waiting for b'Hello, world!'")


def test_expect_bytes_connection_closed(pytester):
    pytester.copy_example("test_expect_bytes_connection_closed.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "Expected to read b'Hello, world' but only read b'' before the connection was closed."
    )


def test_expect_bytes_wrong_bytes_sent(pytester):
    pytester.copy_example("test_expect_bytes_wrong_bytes_sent.py")
    result = pytester.runpytest()
    assert_failure(result, "Expected to read b'Bonjour' but actually read b'Goodbye'")


def test_send_bytes(pytester):
    pytester.copy_example("test_send_bytes.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_sent_data_not_read(pytester):
    pytester.copy_example("test_sent_data_not_read.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "There is data sent by server that was not read by client: unread_bytes=b'Hola!'."
    )


def test_readuntil(pytester):
    pytester.copy_example("test_readuntil.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "There is data sent by server that was not read by client: unread_bytes=b'BBB'."
    )


def test_readline(pytester):
    pytester.copy_example("test_readline.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "There is data sent by server that was not read by client: unread_bytes=b'Two\\n'."
    )


def test_readexactly(pytester):
    pytester.copy_example("test_readexactly.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "There is data sent by server that was not read by client: unread_bytes=b'Two'."
    )


def test_connection_reset_error(pytester):
    pytester.copy_example("test_connection_reset_error.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "Connection was reset. Did client close writer prematurely?"
    )


def test_delayed_join(pytester):
    pytester.copy_example("test_delayed_join.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_expect_connect_is_absent(pytester):
    pytester.copy_example("test_expect_connect_is_absent.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "Missing `expect_connect()` before `expect_bytes(b'Hello, world')`"
    )


def test_early_error_doesnt_hang_test(pytester):
    pytester.copy_example("test_early_error_doesnt_hang_test.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "Expected to read b'Hello' but actually read b'Adios'"
    )


def test_ordering_error(pytester):
    pytester.copy_example("test_ordering_error.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_expect_frame_success(pytester):
    pytester.copy_example("test_expect_frame_success.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_expect_frame_times_out(pytester):
    pytester.copy_example("test_expect_frame_times_out.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "Timed out waiting for frame b'Goodbye, world'"
    )


def test_expect_frame_wrong_bytes_sent(pytester):
    pytester.copy_example("test_expect_frame_wrong_bytes_sent.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "Expected to get frame b'Bonjour' but actually got frame b'Goodbye, world'"
    )


def test_send_frame_success(pytester):
    pytester.copy_example("test_send_frame_success.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_sent_frame_not_read(pytester):
    pytester.copy_example("test_sent_frame_not_read.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "There is data sent by server that was not read by client: " +
        "unread_bytes=b'\\x00\\x00\\x00\\x05Hello'."
    )


def test_server_disconnect(pytester):
    pytester.copy_example("test_server_disconnect.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_readexactly_incomplete(pytester):
    pytester.copy_example("test_readexactly_incomplete.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_tcpserver_factory_success(pytester):
    pytester.copy_example("test_tcpserver_factory_success.py")
    pytester.runpytest().assert_outcomes(passed=1)


def test_tcpserver_factory_second_connection_causes_failure(pytester):
    pytester.copy_example("test_tcpserver_factory_second_connection_causes_failure.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "While waiting for client to disconnect a second connection was attempted.",
        server_variable_name="server",
    )


def test_tcpserver_factory_two_servers_one_fails(pytester):
    pytester.copy_example("test_tcpserver_factory_two_servers_one_fails.py")
    result = pytester.runpytest()
    assert_failure(
        result,
        "Expected to get frame b'Client hello 2' but actually got frame b''",
        server_variable_name="server_2",
    )
