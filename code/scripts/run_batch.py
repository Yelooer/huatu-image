"""Generate every group in a batch file, all groups concurrently. Re-running only fills in missing shots.

Usage: python run_batch.py <batch.json> [group_id ...]
Log:   D:\\xhs\\output\\<batch name>.log
"""
import json
import sys
import time
import pathlib
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import run_group


if __name__ == "__main__":
    batch_path = pathlib.Path(sys.argv[1])
    groups = json.loads(batch_path.read_text(encoding="utf-8"))
    wanted = set(sys.argv[2:])
    if wanted:
        groups = [g for g in groups if g["id"] in wanted]

    log_path = run_group.OUT_ROOT / f"{batch_path.stem}.log"
    lock = threading.Lock()

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        with lock:
            print(line, flush=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    t = time.time()
    with ThreadPoolExecutor(len(groups)) as ex:  # every group at once; the API doesn't cap concurrency
        results = dict(zip((g["id"] for g in groups), ex.map(lambda g: run_group.run(g, log=log), groups)))

    done = [gid for gid, ok in results.items() if all(ok)]
    missing = {gid: [i + 1 for i, v in enumerate(ok) if not v] for gid, ok in results.items() if not all(ok)}
    log(f"DONE {len(done)}/{len(groups)} groups complete in {time.time()-t:.0f}s")
    for gid, shots in missing.items():
        log(f"INCOMPLETE {gid}: missing shots {shots}")
