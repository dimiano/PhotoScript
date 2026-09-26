# AVI RIFF and Windows timestamp updater

from pathlib import Path
import struct
import shutil
import os
import ctypes
from ctypes import wintypes
from datetime import datetime
import calendar

# ============================================================
# SETTINGS
# ============================================================

filename = Path("MVI_5396.avi")

NEW_DATE_TIME = "2009-08-01 18:40:00" # 

# RIFF DateTimeOriginal / IDIT
date_time_original = NEW_DATE_TIME

# RIFF DateCreated / ICRD
date_created = NEW_DATE_TIME

# Windows filesystem timestamps
file_accessed = NEW_DATE_TIME
file_created = NEW_DATE_TIME
file_modified = NEW_DATE_TIME


# ============================================================
# HELPERS
# ============================================================

def parse_datetime(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def make_idit_value(value):
    """
    RIFF IDIT format:

        SAT AUG 01 20:00:00 2009\\n\\0
    """
    dt = parse_datetime(value)
    text = dt.strftime("%a %b %d %H:%M:%S %Y").upper()
    return text.encode("ascii") + b"\n\x00"


def find_chunk(data, chunk_id):
    """
    Find a RIFF chunk by its 4-byte ID and return:

        offset, size, payload

    """
    pos = data.find(chunk_id)

    if pos == -1:
        raise RuntimeError(f"{chunk_id.decode('ascii')} chunk not found")

    if pos + 8 > len(data):
        raise RuntimeError(f"Invalid {chunk_id.decode('ascii')} chunk")

    size = struct.unpack_from("<I", data, pos + 4)[0]

    end = pos + 8 + size

    if end > len(data):
        raise RuntimeError(
            f"{chunk_id.decode('ascii')} chunk extends beyond file"
        )

    payload = bytes(data[pos + 8:end])

    return pos, size, payload


def replace_chunk(data, chunk_id, new_value):
    """
    Replace a chunk payload without changing its size.
    """

    pos, size, old_value = find_chunk(data, chunk_id)

    print()
    print(f"{chunk_id.decode('ascii')} offset: 0x{pos:X}")
    print(f"{chunk_id.decode('ascii')} size:   {size}")
    print(f"Old value: {old_value!r}")
    print(f"New value: {new_value!r}")

    if len(new_value) != size:
        raise RuntimeError(
            f"{chunk_id.decode('ascii')} is {size} bytes, "
            f"but new value is {len(new_value)} bytes. "
            f"Refusing to modify it."
        )

    data[pos + 8:pos + 8 + size] = new_value


def datetime_to_filetime(value):
    """
    Convert YYYY-MM-DD HH:MM:SS to Windows FILETIME.
    """

    dt = parse_datetime(value)

    # Interpret supplied time as UTC.
    timestamp = calendar.timegm(dt.timetuple())

    # Seconds between 1601-01-01 and 1970-01-01.
    WINDOWS_EPOCH_OFFSET = 11644473600

    return (timestamp + WINDOWS_EPOCH_OFFSET) * 10_000_000


# ============================================================
# READ AVI
# ============================================================

data = bytearray(filename.read_bytes())


# ============================================================
# UPDATE RIFF DateTimeOriginal / IDIT
# ============================================================

new_idit = make_idit_value(date_time_original)

try:
    replace_chunk(data, b"IDIT", new_idit)

except Exception as err:
    print(f"Error replacing IDIT chunk: {err=}, {type(err)=}")

# ============================================================
# UPDATE RIFF DateCreated / ICRD
# ============================================================

# ICRD is normally stored as an ASCII date string terminated
# by NUL. We preserve the existing chunk size.

try:
    _, icrd_size, old_icrd = find_chunk(data, b"ICRD")

    new_icrd_text = date_created.encode("ascii") + b"\x00"

    print()
    print("ICRD")
    print(f"ICRD size: {icrd_size}")
    print(f"Old value: {old_icrd!r}")
    print(f"New value: {new_icrd_text!r}")

    if len(new_icrd_text) != icrd_size:
        raise RuntimeError(
            f"ICRD is {icrd_size} bytes, but the new DateCreated "
            f"value is {len(new_icrd_text)} bytes."
        )

    replace_chunk(
        data,
        b"ICRD",
        new_icrd_text
    )
except Exception as err:
    print(f"Error updating ICRD: {err=}, {type(err)=}")

# ============================================================
# BACKUP
# ============================================================

# backup = filename.with_suffix(filename.suffix + ".bak")

# if not backup.exists():
    # shutil.copy2(filename, backup)
    # print()
    # print(f"Backup created: {backup}")
# else:
    # print()
    # print(f"Backup already exists: {backup}")


# ============================================================
# WRITE AVI
# ============================================================

filename.write_bytes(data)

print()
print("RIFF metadata updated.")


# ============================================================
# WINDOWS FILESYSTEM TIMESTAMPS
# ============================================================

class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]


def make_filetime(value):
    ft = datetime_to_filetime(value)

    return FILETIME(
        ft & 0xFFFFFFFF,
        (ft >> 32) & 0xFFFFFFFF
    )


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


CreateFileW = kernel32.CreateFileW
CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]
CreateFileW.restype = wintypes.HANDLE


SetFileTime = kernel32.SetFileTime
SetFileTime.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(FILETIME),
    ctypes.POINTER(FILETIME),
    ctypes.POINTER(FILETIME),
]
SetFileTime.restype = wintypes.BOOL


CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]


GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000

FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004

OPEN_EXISTING = 3


handle = CreateFileW(
    str(filename),
    GENERIC_READ | GENERIC_WRITE,
    FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
    None,
    OPEN_EXISTING,
    0,
    None
)

if handle == wintypes.HANDLE(-1).value:
    error = ctypes.get_last_error()
    raise ctypes.WinError(error)


try:
    creation_ft = make_filetime(file_created)
    access_ft = make_filetime(file_accessed)
    modified_ft = make_filetime(file_modified)

    if not SetFileTime(
        handle,
        ctypes.byref(creation_ft),
        ctypes.byref(access_ft),
        ctypes.byref(modified_ft)
    ):
        error = ctypes.get_last_error()
        raise ctypes.WinError(error)

finally:
    CloseHandle(handle)


print()
print("Filesystem timestamps updated:")
print(f"  Creation : {file_created}")
print(f"  Access   : {file_accessed}")
print(f"  Modified : {file_modified}")
print()
print("Done.")
