# AVI RIFF IDIT timestamp removal from the INFO list

import struct
import shutil
from pathlib import Path


INPUT_FILE = Path("2008-04-01_19-29_001.avi")


def read_u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def write_u32(data, offset, value):
    struct.pack_into("<I", data, offset, value)


def chunk_total_size(payload_size):
    # 4-byte ID + 4-byte size + payload + optional RIFF padding byte
    return 8 + payload_size + (payload_size & 1)


def find_info_list(data):
    """
    Find the INFO LIST in the RIFF AVI file.

    Returns:
        list_offset
        list_size
        children_start
        list_end
    """

    if data[0:4] != b"RIFF":
        raise ValueError("Not a RIFF file.")

    if data[8:12] != b"AVI ":
        raise ValueError("Not an AVI file.")

    pos = 12

    while pos + 12 <= len(data):

        chunk_id = data[pos:pos + 4]
        size = read_u32(data, pos + 4)

        if chunk_id == b"LIST":

            if pos + 12 > len(data):
                raise ValueError(
                    f"Truncated LIST at 0x{pos:X}"
                )

            list_type = data[pos + 8:pos + 12]

            if list_type == b"INFO":

                list_end = pos + 8 + size

                if list_end > len(data):
                    raise ValueError(
                        "INFO LIST extends beyond end of file."
                    )

                return (
                    pos,
                    size,
                    pos + 12,
                    list_end
                )

        total = chunk_total_size(size)

        if pos + total > len(data):
            raise ValueError(
                f"Invalid RIFF structure at 0x{pos:X}."
            )

        pos += total

    raise ValueError("INFO LIST not found.")


def find_idit_chunks(data, start, end):
    """
    Find IDIT chunks directly inside the specified LIST.
    """

    results = []

    pos = start

    while pos + 8 <= end:

        chunk_id = data[pos:pos + 4]
        size = read_u32(data, pos + 4)

        total = chunk_total_size(size)

        if pos + total > end:
            raise ValueError(
                f"Chunk at 0x{pos:X} extends beyond LIST."
            )

        if chunk_id == b"IDIT":

            payload_offset = pos + 8

            payload = data[
                payload_offset:
                payload_offset + size
            ]

            results.append({
                "offset": pos,
                "size": size,
                "total_size": total,
                "payload": payload,
            })

        pos += total

    return results


def remove_info_idit(filename):

    filename = Path(filename)

    if not filename.exists():
        raise FileNotFoundError(filename)

    data = bytearray(filename.read_bytes())

    original_file_size = len(data)

    # --------------------------------------------------------
    # Find INFO LIST
    # --------------------------------------------------------

    info_offset, info_size, info_start, info_end = \
        find_info_list(data)

    print(f"INFO LIST offset : 0x{info_offset:X} ({info_offset})")
    print(f"INFO LIST size   : {info_size}")

    # --------------------------------------------------------
    # Find IDIT inside INFO
    # --------------------------------------------------------

    idits = find_idit_chunks(
        data,
        info_start,
        info_end
    )

    print(f"IDIT chunks in INFO: {len(idits)}")

    if len(idits) == 0:
        raise ValueError(
            "No IDIT chunk was found inside the INFO LIST."
        )

    if len(idits) > 1:
        raise ValueError(
            "More than one IDIT exists inside INFO. "
            "Script stopped to avoid removing the wrong one."
        )

    target = idits[0]

    target_offset = target["offset"]
    target_size = target["size"]
    target_total_size = target["total_size"]

    try:
        target_text = target["payload"].rstrip(
            b"\x00"
        ).decode("ascii")
    except UnicodeDecodeError:
        target_text = repr(target["payload"])

    print()
    print("IDIT inside INFO:")
    print(f"  Offset       : 0x{target_offset:X}")
    print(f"  Payload size : {target_size}")
    print(f"  Total size   : {target_total_size}")
    print(f"  Value        : {target_text!r}")

    # --------------------------------------------------------
    # Safety checks
    # --------------------------------------------------------

    if target_size != 26:
        raise ValueError(
            f"Unexpected IDIT payload size: {target_size}. "
            f"Expected 26. Nothing was changed."
        )

    expected = b"TUE APR 01 20:00:16 2008\n\x00"

    if target["payload"] != expected:

        raise ValueError(
            "The IDIT inside INFO does not contain the "
            "expected 20:00:16 timestamp.\n"
            f"Actual bytes: {target['payload']!r}\n"
            f"Expected:     {expected!r}\n\n"
            "Nothing was changed."
        )

    # --------------------------------------------------------
    # Remove the IDIT chunk
    # --------------------------------------------------------

    print()
    print("Removing IDIT from INFO...")

    del data[
        target_offset:
        target_offset + target_total_size
    ]

    # --------------------------------------------------------
    # Update INFO LIST size
    # --------------------------------------------------------

    new_info_size = info_size - target_total_size

    write_u32(
        data,
        info_offset + 4,
        new_info_size
    )

    # --------------------------------------------------------
    # Update RIFF size
    # --------------------------------------------------------

    old_riff_size = read_u32(data, 4)

    new_riff_size = old_riff_size - target_total_size

    write_u32(
        data,
        4,
        new_riff_size
    )

    # --------------------------------------------------------
    # Create backup
    # --------------------------------------------------------

    backup = filename.with_suffix(
        filename.suffix + ".bak"
    )

    if backup.exists():
        raise FileExistsError(
            f"Backup already exists:\n"
            f"{backup}\n\n"
            f"Delete or rename it before running the script again."
        )

    shutil.copy2(filename, backup)

    # --------------------------------------------------------
    # Write modified file
    # --------------------------------------------------------

    filename.write_bytes(data)

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SUCCESS")
    print("=" * 60)

    print(f"Backup          : {backup}")
    print(f"Original size   : {original_file_size} bytes")
    print(f"New size        : {len(data)} bytes")
    print(f"Removed         : {target_total_size} bytes")

    print(
        f"INFO size       : "
        f"{info_size} -> {new_info_size}"
    )

    print(
        f"RIFF size       : "
        f"{old_riff_size} -> {new_riff_size}"
    )

    print()
    print("The IDIT inside INFO was removed.")
    print("The original 19:29:16 IDIT was preserved.")
    print("Video/audio streams were not re-encoded.")


if __name__ == "__main__":
    remove_info_idit(INPUT_FILE)
    