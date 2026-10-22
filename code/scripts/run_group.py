"""Generate one 5-shot group with gpt-image-2.5.

References: the character face sheet locks the face for every shot; shot 1 also fixes the group's outfit,
hair and makeup, so shots 2+ reference [sheet, shot 1] and run concurrently. A shot may override
服装/妆容/发型 (fitting-room or before/after groups); those then follow the text instead of shot 1.
Shot 1 (the cover) is generated COVERS times into <out>/_covers/c1_*, c2_*...; c1 is copied to 01_* and
anchors shots 2+. pick_cover.py swaps in another candidate later.
Existing outputs are kept, so re-running a group only fills in missing shots.
Usage: python run_group.py <group.json> [gpt25|gpt2high]
Output: D:\\xhs\\output\\<group id>\\NN_<name>.<ext>  plus prompts.md (the shareable prompts).
"""
import json
import sys
import time
import pathlib
import shutil
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import imgapi
import strip_c2pa

CHAR = json.loads(pathlib.Path(r"D:\xhs\character\yao.json").read_text(encoding="utf-8"))
OUT_ROOT = pathlib.Path(r"D:\xhs\output")
ORDER = ["主体", "五官", "妆容", "肤质", "发型", "饰品", "身材", "服装", "环境"]
FACE_LOCK = "即使表情夸张或拍摄角度很大，脸型和五官也要与设定图保持一致。"
OVERRIDABLE = ("服装", "妆容", "发型", "画质")
ANCHOR_PREFIX = ("参考图是这个女生的人物设定图（同一个人的多个角度）。请生成她的一张真实生活照："
                 "脸（脸型、五官、泪痣）与设定图完全一致；发型、妆容和服装按下面的文字描述。" + FACE_LOCK + "\n")
WORKERS = 4
COVERS = 3
MODELS = {"gpt25": imgapi.gpt25, "gpt2high": imgapi.gpt}  # gpt() defaults to gpt-image-2-high at 4K
MODEL = "gpt25"


class Unsafe(RuntimeError):
    pass


def blocks_for(group, shot):
    b = {**CHAR["blocks"], **group["blocks"]}
    b.update({k: shot[k] for k in OVERRIDABLE if k in shot})
    return b


def share_prompt(group, shot):
    b = blocks_for(group, shot)
    lines = [f"【{k}】{b[k]}" for k in ORDER if k in b]
    if "场景" in shot:
        lines.append(f"【场景】{shot['场景']}")
    lines += [f"【镜头】{shot['镜头']}", f"【光线】{shot['光线']}", f"【画质】{b['画质']}"]
    return "\n".join(lines)


def shot_prefix(shot):
    from_text = [k for k in ("发型", "妆容", "服装") if k in shot]
    from_ref = [k for k in ("发型", "妆容", "服装") if k not in from_text]
    s = "图1是这个女生的人物设定图；图2是她同一天的另一张照片。脸（脸型、五官、泪痣）与图1一致"
    if from_ref:
        s += f"；{'、'.join(from_ref)}与图2一致"
    if from_text:
        s += f"；{'、'.join(from_text)}按下面的文字描述，不要照搬图2"
    return (s + "。不要复制图2的场景、构图、姿势和拍摄角度，严格按下面描述的新场景、新姿势和新机位拍摄。"
            + FACE_LOCK + "\n")


def internal_prompt(prefix, group, shot):
    """Prefix + a restated pose/framing up front (models weight the start most) + the shareable prompt."""
    focus = f"这张照片的重点：{shot.get('场景', '')}{shot['镜头']}\n\n"
    return prefix + focus + share_prompt(group, shot)


def ext_of(data):
    return ".jpg" if data[:3] == b"\xff\xd8\xff" else ".webp" if data[8:12] == b"WEBP" else ".png"


def call(prompt, refs, tries=5):
    for i in range(tries):
        try:
            return MODELS[MODEL](prompt, refs=refs)
        except Exception as e:
            msg = str(e)
            if "451" in msg or "unsafe" in msg:
                raise Unsafe(msg[:200])
            # retry rate limits, timeouts, 5xx and dropped connections; other 4xx won't fix themselves
            # safety rejections are partly random, so give them two more tries
            retryable = "429" in msg or not msg.startswith("gpt 4") or ("content_policy" in msg and i < 2)
            if retryable and i < tries - 1:
                time.sleep(20 * (i + 1))
                continue
            raise


def existing(out, prefix):
    return next(iter(sorted(out.glob(f"{prefix}_*"))), None)


def gen(out, prefix, shot, prompt, refs, label=None):
    """Write <out>/<prefix>_<shot name>.<ext> unless it already exists."""
    label = f"{label or out.name} {prefix}"
    t = time.time()
    if (done := existing(out, prefix)):
        return done, f"{label} skip (exists)"
    try:
        data, _ = strip_c2pa.strip_bytes(call(prompt, refs))
        path = out / f"{prefix}_{shot['name']}{ext_of(data)}"
        path.write_bytes(data)
        return path, f"{label} ok {time.time()-t:.0f}s"
    except Unsafe as e:
        return None, f"{label} UNSAFE: {e}"
    except Exception as e:
        return None, f"{label} FAILED {time.time()-t:.0f}s: {e}"


def make_cover(group, out, log):
    """Generate COVERS candidates for shot 1 concurrently; the first one that succeeds becomes 01_*."""
    if (done := existing(out, "01")):
        return done
    shot = group["shots"][0]
    prompt = internal_prompt(ANCHOR_PREFIX, group, shot)
    cdir = out / "_covers"
    cdir.mkdir(exist_ok=True)
    with ThreadPoolExecutor(COVERS) as ex:
        futs = [ex.submit(gen, cdir, f"c{i}", shot, prompt, [CHAR["sheet"]], out.name) for i in range(1, COVERS + 1)]
        results = [f.result() for f in futs]
    for _, m in results:
        log(m)
    first = next((p for p, _ in results if p), None)
    if first:
        dst = out / f"01_{shot['name']}{first.suffix}"
        shutil.copyfile(first, dst)
        return dst
    return None


def write_prompts(group, out):
    parts = [f"# {group['title']}\n"]
    for i, s in enumerate(group["shots"], start=1):
        parts.append(f"## 图{i}｜{s['name']}\n\n{share_prompt(group, s)}\n")
    (out / "prompts.md").write_text("\n".join(parts), encoding="utf-8")


def out_dir(group):
    out = OUT_ROOT / group["id"]
    return out if MODEL == "gpt25" else out.with_name(f"{out.name}_{MODEL}")


def run(group, log=print):
    """Generate a group; returns the list of log lines' success flags (True per finished shot)."""
    out = out_dir(group)
    out.mkdir(parents=True, exist_ok=True)
    write_prompts(group, out)
    sheet = CHAR["sheet"]
    shots = group["shots"]

    if COVERS > 1:
        anchor = make_cover(group, out, log)
    else:
        anchor, msg = gen(out, "01", shots[0], internal_prompt(ANCHOR_PREFIX, group, shots[0]), [sheet])
        log(msg)
    if not anchor:
        return [False] * len(shots)
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = [ex.submit(gen, out, f"{i:02d}", s, internal_prompt(shot_prefix(s), group, s), [sheet, str(anchor)])
                for i, s in enumerate(shots[1:], start=2)]
        results = [f.result() for f in futs]
    for _, m in results:
        log(m)
    return [True] + [p is not None for p, _ in results]


if __name__ == "__main__":
    group = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    if len(sys.argv) > 2:
        MODEL = sys.argv[2]
    ok = run(group, log=lambda m: print(m, flush=True))
    sys.exit(0 if all(ok) else 1)
