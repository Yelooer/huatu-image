"""Build a month of groups from series specs (D:/xhs/groups/month01/*.py) into one batch file.

Each series spec has outfits x scenes; every (scene, outfit) pair is one group with its own hook title.
Groups are interleaved into a publishing schedule: PER_DAY posts a day, PROVEN_PER_DAY of them from the
proven series and the rest from the experiments, so the same scene comes back about once a week.
Group ids are assigned in publishing order and each group carries its date and slot.
Usage: python make_month.py <spec dir> <out batch.json> <first day YYYY-MM-DD> <first id number> [existing.json]
  existing.json: groups already made (e.g. tests) that fill slots named in a spec's "existing" map.
"""
import datetime
import importlib.util
import json
import pathlib
import sys

PER_DAY, PROVEN_PER_DAY = 10, 7
BASE_TAGS = ["AI写真", "AI绘画", "提示词分享"]
COVER_TAIL = "正脸看镜头，平视，全身，人物在画面中央，从头到脚完整入镜。"
LIGHT_MAKEUP = ("清透的淡妆，妆面干爽：轻薄的雾面底妆，扑了散粉，是哑光质感，额头、鼻头和脸颊没有任何反光点；"
                "淡棕色平眉；浅浅的大地色眼影和根根分明的睫毛；淡淡的蜜桃色哑光腮红；豆沙粉色雾面唇。")


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SERIES


def build(series, si, oi):
    sc, of = series["scenes"][si], series["outfits"][oi]
    title, intro = series["titles"][si][oi]
    blocks = {"服装": of["服装"], "环境": sc["env"]}
    for key in ("发型", "妆容"):
        val = of.get(key, series.get(key))
        if val:
            blocks[key] = LIGHT_MAKEUP if val == "LIGHT" else val
    shots = []
    for k, (name, place, cam, light, brief) in enumerate(sc["shots"]):
        if k == 0:
            cam = cam.rstrip("，。") + "，" + COVER_TAIL
        shots.append({"name": name, "场景": place, "镜头": cam, "光线": light or sc["light"], "简述": brief})
    g = {
        "id": None,
        "series": series["name"],
        "attrs": {"系列": series["name"], "穿搭": of["label"], "露肤": of["露肤"],
                  "封面": "坐" if "坐" in sc["shots"][0][2][:12] else "站",
                  "背景": sc.get("bg", "明亮"), "风格": series["style"]},
        "title": title,
        "intro": intro,
        "outfit_short": of["short"],
        "tip": sc["tip"],
        "tags": BASE_TAGS + series["tags"],
        "blocks": blocks,
        "shots": shots,
    }
    mk = of.get("妆_short", series.get("妆_short"))
    hr = of.get("发_short", series.get("发_short"))
    if mk or hr:
        g["妆发_short"] = f"{mk or '精致全妆'}；{hr or '黑茶色长发+八字刘海'}"
    return g


def series_queue(series, existing):
    """Groups of one series in posting order: outfit-major so a scene repeats only after len(scenes) posts."""
    q = [existing[gid] for gid in series.get("existing", {}).values()]
    skip = set(series.get("existing", {}))
    for oi in range(len(series["outfits"])):
        for si in range(len(series["scenes"])):
            if f"{si},{oi}" not in skip:
                g = build(series, si, oi)
                g["_slug"] = f"{series['slug']}{si + 1}{chr(97 + oi)}"
                q.append(g)
    return q


def interleave(queues):
    """Spread several queues evenly: item i of a queue of length n sorts at (i + 0.5) / n."""
    keyed = [((i + 0.5) / len(q), k, g) for k, q in enumerate(queues) for i, g in enumerate(q)]
    return [g for _, _, g in sorted(keyed, key=lambda t: (t[0], t[1]))]


if __name__ == "__main__":
    spec_dir, out, first_day, first_id = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4])
    existing = {}
    if len(sys.argv) > 5:
        existing = {g["id"]: g for g in json.loads(pathlib.Path(sys.argv[5]).read_text(encoding="utf-8"))}
    specs = [load(p) for p in sorted(spec_dir.glob("*.py"))]
    proven = interleave([series_queue(s, existing) for s in specs if s["pool"] == "proven"])
    trial = interleave([series_queue(s, existing) for s in specs if s["pool"] == "trial"])

    day0 = datetime.date.fromisoformat(first_day)
    schedule, n = [], first_id
    days = (len(proven) + len(trial) + PER_DAY - 1) // PER_DAY
    for d in range(days):
        today = proven[d * PROVEN_PER_DAY:(d + 1) * PROVEN_PER_DAY]
        extra = trial[d * (PER_DAY - PROVEN_PER_DAY):(d + 1) * (PER_DAY - PROVEN_PER_DAY)]
        # proven, trial, proven, proven, trial ... so experiments are spread through the day
        mixed = []
        for i in range(max(len(today), 1) + len(extra)):
            if extra and i % 3 == 1:
                mixed.append(extra.pop(0))
            elif today:
                mixed.append(today.pop(0))
        mixed += today + extra
        for slot, g in enumerate(mixed, start=1):
            if g["id"] is None:
                g["id"] = f"g{n:03d}_{g.pop('_slug')}"
                n += 1
            g["date"] = (day0 + datetime.timedelta(days=d)).isoformat()
            g["slot"] = slot
            schedule.append(g)
    pathlib.Path(out).write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")
    titles = [g["title"] for g in schedule]
    dup = {t for t in titles if titles.count(t) > 1}
    print(f"{len(schedule)} groups over {days} days -> {out}; ids up to g{n - 1:03d}")
    if dup:
        print("DUPLICATE TITLES:", dup)
