"""Generate a big batch in waves of WAVE groups (one wave at a time keeps memory use down).

Skips groups that already have 5 shots; re-running fills in whatever is missing.
Usage: python run_month.py <batch.json> [wave size]
"""
import json
import subprocess
import sys
import pathlib

OUT = pathlib.Path(r"D:\xhs\output")

if __name__ == "__main__":
    batch = sys.argv[1]
    wave = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    groups = json.loads(pathlib.Path(batch).read_text(encoding="utf-8"))
    todo = [g["id"] for g in groups if len(list((OUT / g["id"]).glob("0*.png"))) < len(g["shots"])]
    print(f"{len(todo)} groups to do, waves of {wave}", flush=True)
    for i in range(0, len(todo), wave):
        ids = todo[i:i + wave]
        print(f"== wave {i // wave + 1}: {ids[0]} .. {ids[-1]}", flush=True)
        subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "run_batch.py"), batch, *ids])
