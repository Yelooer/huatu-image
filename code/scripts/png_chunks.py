"""List PNG chunks (type, size, and a peek at text chunks) to see what metadata an image carries."""
import struct
import sys


def chunks(path):
    with open(path, "rb") as f:
        assert f.read(8) == b"\x89PNG\r\n\x1a\n", "not a PNG"
        while True:
            head = f.read(8)
            if len(head) < 8:
                return
            length, ctype = struct.unpack(">I4s", head)
            data = f.read(length)
            f.read(4)  # crc
            yield ctype.decode("latin-1"), data


for path in sys.argv[1:]:
    print(path)
    for ctype, data in chunks(path):
        if ctype == "IDAT":
            continue
        peek = data[:160].decode("latin-1", "replace").replace("\x00", "|") if ctype in ("tEXt", "iTXt", "zTXt") else ""
        print(f"  {ctype:5} {len(data):>9}  {peek}")
