"""Use cover candidate N as a group's shot 1 (replaces 01_*).

Usage: python pick_cover.py <group_id> <n> [<group_id> <n> ...]
"""
import sys
import shutil
import pathlib

OUT_ROOT = pathlib.Path(r"D:\xhs\output")

if __name__ == "__main__":
    args = sys.argv[1:]
    for gid, n in zip(args[::2], args[1::2]):
        out = OUT_ROOT / gid
        src = next(iter(sorted((out / "_covers").glob(f"c{n}_*"))), None)
        if not src:
            print(f"{gid}: no candidate c{n}")
            continue
        for old in out.glob("01_*"):
            old.unlink()
        dst = out / f"01_{src.name.split('_', 1)[1]}"
        shutil.copyfile(src, dst)
        print(f"{gid}: cover = c{n}")
