"""Check batch files before spending money on generation.

Per group: required fields, 5 shots, title <= 20 chars, body <= 1000 chars, at least 3 distinct camera
angles, at least one full-body and one close shot, a full-body cover (groups with a series), and no id/title clash with other batches.
Usage: python validate_batch.py <batch.json> [...]
"""
import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build_posts

GROUP_KEYS = ("id", "title", "intro", "outfit_short", "tip", "tags", "blocks", "shots")
SHOT_KEYS = ("name", "镜头", "光线", "简述")
ANGLES = ("俯拍", "仰拍", "平视", "侧面", "背", "侧后方", "斜后方", "斜上方", "正上方", "低机位", "长焦", "对面", "侧前方")
FULL = ("全身",)
CLOSE = ("特写", "近景")


def check(groups, seen_ids, seen_titles):
    errs = []
    for g in groups:
        gid = g.get("id", "?")
        errs += [f"{gid}: missing {k}" for k in GROUP_KEYS if k not in g]
        if gid in seen_ids:
            errs.append(f"{gid}: duplicate id")
        if g.get("title") in seen_titles:
            errs.append(f"{gid}: duplicate title {g['title']}")
        seen_ids.add(gid)
        seen_titles.add(g.get("title"))
        shots = g.get("shots", [])
        if len(shots) != 5:
            errs.append(f"{gid}: {len(shots)} shots")
        for i, s in enumerate(shots, 1):
            errs += [f"{gid} shot{i}: missing {k}" for k in SHOT_KEYS if k not in s]
        cams = " ".join(s.get("镜头", "") for s in shots)
        skip = set(g.get("skip_checks", []))  # e.g. a makeup lesson is all close-ups by design
        n_angles = sum(a in cams for a in ANGLES)
        if n_angles < 3 and "angles" not in skip:
            errs.append(f"{gid}: only {n_angles} camera angles")
        if not any(f in cams for f in FULL) and "full" not in skip:
            errs.append(f"{gid}: no full-body shot")
        if not any(c in cams for c in CLOSE) and "close" not in skip:
            errs.append(f"{gid}: no close-up shot")
        if "series" in g and shots and "全身" not in shots[0].get("镜头", ""):
            errs.append(f"{gid}: cover (shot 1) must be full-body")
        if len(g.get("title", "")) > build_posts.TITLE_MAX:
            errs.append(f"{gid}: title {len(g['title'])} chars")
        if all(k in g for k in GROUP_KEYS) and len(build_posts.body_of(g)) > build_posts.BODY_MAX:
            errs.append(f"{gid}: body {len(build_posts.body_of(g))} chars")
    return errs


if __name__ == "__main__":
    seen_ids, seen_titles = set(), set()
    for old in sorted(pathlib.Path(r"D:\xhs\groups").glob("batch*.json")):
        if old.resolve() not in {pathlib.Path(a).resolve() for a in sys.argv[1:]}:
            for g in json.loads(old.read_text(encoding="utf-8")):
                seen_ids.add(g["id"]); seen_titles.add(g["title"])
    total = 0
    for path in sys.argv[1:]:
        groups = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        total += len(groups)
        for e in check(groups, seen_ids, seen_titles):
            print("ERR", pathlib.Path(path).name, e)
    print(f"checked {total} groups")
