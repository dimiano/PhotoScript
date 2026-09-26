# Inspect metadata chunk named IDIT (RIFF tag) in an AVI file.

from pathlib import Path
import struct

filename = "2008-04-01_19-29_001.avi"

data = Path(filename).read_bytes()

pos = data.find(b"IDIT")

if pos == -1:
    raise SystemExit("IDIT chunk not found")

size = struct.unpack_from("<I", data, pos + 4)[0]
value = data[pos + 8:pos + 8 + size]

print(f"IDIT offset : 0x{pos:X} ({pos})")
print(f"IDIT size   : {size}")
print(f"Raw bytes   : {value.hex(' ')}")
print(f"ASCII       : {value!r}")