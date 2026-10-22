"""Remove C2PA manifests from PNG / JPEG files without touching pixel data.

PNG : drops the `caBX` chunk (C2PA JUMBF box). Pixel chunks (IDAT) are copied byte-for-byte,
      so invisible watermarks such as SynthID survive.
JPEG: drops APP11 segments that carry JUMBF / C2PA. Entropy-coded data is copied as-is.

Usage: python strip_c2pa.py <file or folder> [...]   (folders are processed recursively)
"""
import os
import struct
import sys
import pathlib

PNG_SIG = b"\x89PNG\r\n\x1a\n"
PNG_DROP = {b"caBX"}


def strip_png(data):
    if not data.startswith(PNG_SIG):
        raise ValueError("not a PNG")
    out, pos, removed = [PNG_SIG], 8, 0
    while pos < len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        end = pos + 12 + length
        if ctype in PNG_DROP:
            removed += 1
        else:
            out.append(data[pos:end])
        pos = end
        if ctype == b"IEND":
            break
    return b"".join(out), removed


def strip_jpeg(data):
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG")
    out, pos, removed = [data[:2]], 2, 0
    while pos < len(data):
        if data[pos] != 0xFF:
            raise ValueError(f"bad JPEG marker at {pos}")
        marker = data[pos + 1]
        if marker == 0xDA:  # start of scan: the rest is image data
            out.append(data[pos:])
            break
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        seg = data[pos:pos + 2 + length]
        if marker == 0xEB and (b"jumb" in seg or b"c2pa" in seg):
            removed += 1
        else:
            out.append(seg)
        pos += 2 + length
    return b"".join(out), removed


def strip_bytes(data):
    """Return (clean bytes, number of C2PA blocks removed). Unknown formats pass through unchanged."""
    if data.startswith(PNG_SIG):
        return strip_png(data)
    if data[:2] == b"\xff\xd8":
        return strip_jpeg(data)
    return data, 0


def strip_file(path):
    path = pathlib.Path(path)
    data = path.read_bytes()
    clean, removed = strip_bytes(data)
    if removed:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(clean)
        os.replace(tmp, path)
    return removed


def iter_images(targets):
    for t in map(pathlib.Path, targets):
        if t.is_dir():
            yield from (p for p in sorted(t.rglob("*")) if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
        elif t.is_file():
            yield t


if __name__ == "__main__":
    targets = sys.argv[1:]
    if not targets:
        print("用法：把图片或文件夹拖到 strip_c2pa.bat 上，或运行 python strip_c2pa.py <文件/文件夹>")
        sys.exit(1)
    total = cleaned = 0
    for p in iter_images(targets):
        total += 1
        try:
            n = strip_file(p)
            cleaned += bool(n)
            print(f"{'已清除' if n else '无C2PA'}  {p}")
        except Exception as e:
            print(f"失败    {p}: {e}")
    print(f"\n共 {total} 张，清除了 {cleaned} 张的 C2PA。")
