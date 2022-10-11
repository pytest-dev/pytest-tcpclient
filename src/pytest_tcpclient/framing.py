import asyncio
import struct


def write_frame(writer, payload: bytes):
    writer.write(struct.pack(">I", len(payload)))
    writer.write(payload)


async def read_frame(reader):
    """Read a frame and return the payload. If the connection was closed
    cleanly, meaning that there is no partial message, an empty byte array
    is returned.
    """
    try:
        header_bytes = await reader.readexactly(4)
    except asyncio.IncompleteReadError as e:
        if len(e.partial) == 0:
            return b""
        raise
    message_length, = struct.unpack(">I", header_bytes)
    return await reader.readexactly(message_length)
