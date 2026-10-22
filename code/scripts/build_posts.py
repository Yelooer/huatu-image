"""Package finished groups into the publish repo: posts/<id>/01.png..NN.png + post.md.

Only complete groups are packaged. Images are re-checked for C2PA, and title/body lengths are validated
against Xiaohongshu limits (title <= 20 chars, body <= 1000 chars).
Usage: python build_posts.py <batch.json> [group_id ...]
"""
import datetime
import json
import shutil
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import strip_c2pa

CHAR = json.loads(pathlib.Path(r"D:\xhs\character\yao.json").read_text(encoding="utf-8"))
OUT_ROOT = pathlib.Path(r"D:\xhs\output")
REPO_POSTS = pathlib.Path(r"D:\xhs\huatu-image\posts")
FIRST_DAY = datetime.date(2026, 10, 16)  # g001 = day 1
TITLE_MAX, BODY_MAX = 20, 1000


def body_of(g):
    s = CHAR["short"]
    lines = [g["intro"], "📌 本篇图片均使用AI提示词制作", "整组提示词放下面了，复制就能用👇", "",
             f"【人物】{s['人物']}",
             f"【妆发】{g.get('妆发_short', s['妆发'])}",
             f"【穿搭】{g['outfit_short']}",
             f"【画质】{s['画质']}", ""]
    lines += [f"图{i}｜{sh['name']}：{sh['简述']}" for i, sh in enumerate(g["shots"], start=1)]
    lines += ["", f"💡小技巧：{g['tip']}", "", " ".join(f"#{t}" for t in g["tags"])]
    return "\n".join(lines)


def post_md(g, images, order):
    # month batches carry their own date and slot (10 a day); older batches were one a day by id
    day = datetime.date.fromisoformat(g["date"]) if "date" in g else FIRST_DAY + datetime.timedelta(days=order - 1)
    when = f"{day.isoformat()} 第 {g['slot']} 篇（每天 10 篇）" if "slot" in g else f"{day.isoformat()}（按每天 1 篇排，节日主题已对齐日期）"
    front = "\n".join([
        "---",
        f"id: {g['id']}",
        "series: 瑶的日常",
        f"title: {g['title']}",
        f"order: {order}",
        f"suggested_date: {day.isoformat()}",
        *([f"slot: {g['slot']}"] if "slot" in g else []),
        f"cover: {images[0]}",
        f"images: [{', '.join(images)}]",
        f"tags: [{', '.join(g['tags'])}]",
        "ai_generated: true",
        "status: ready",
        "---",
    ])
    scenes = "；".join(f"{sh['name']}（{sh.get('场景', '').rstrip('。')}）" for sh in g["shots"])
    notes = "\n".join([
        "# 发布说明（给发布 AI 看，不要发出去）", "",
        "- 账号定位：AI 提示词分享号。固定虚拟人物「瑶」的生活组图，正文附上生成这组图的提示词。",
        f"- 本组主题：{g['intro']}",
        f"- 场景：{g['blocks'].get('环境', '')}",
        f"- 五张图依次是：{scenes}。",
        f"- 图片顺序就是发布顺序，`{images[0]}` 是封面。标题用 front matter 的 `title`，正文原样使用下面「正文」一节。",
        f"- 建议发布日期 {when}。",
        "- 发布时请勾选「内容含 AI 生成」的声明。",
    ])
    table = ["| 文件 | 画面 |", "|---|---|"]
    table += [f"| {img}{'（封面）' if i == 0 else ''} | {sh['简述']} |" for i, (img, sh) in enumerate(zip(images, g["shots"]))]
    return f"{front}\n\n{notes}\n\n# 正文\n\n{body_of(g)}\n\n# 每张图说明\n\n" + "\n".join(table) + "\n"


def order_of(gid):
    return int(gid[1:4])


if __name__ == "__main__":
    groups = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    wanted = set(sys.argv[2:])
    problems = []
    for g in groups:
        if wanted and g["id"] not in wanted:
            continue
        src = sorted((OUT_ROOT / g["id"]).glob("0*.png"))
        if len(src) < len(g["shots"]):
            problems.append(f"{g['id']}: only {len(src)}/{len(g['shots'])} images, skipped")
            continue
        if len(g["title"]) > TITLE_MAX:
            problems.append(f"{g['id']}: title {len(g['title'])} chars > {TITLE_MAX}")
        body = body_of(g)
        if len(body) > BODY_MAX:
            problems.append(f"{g['id']}: body {len(body)} chars > {BODY_MAX}")

        dst = REPO_POSTS / g["id"]
        dst.mkdir(parents=True, exist_ok=True)
        images = []
        for i, p in enumerate(src, start=1):
            name = f"{i:02d}.png"
            shutil.copyfile(p, dst / name)
            if strip_c2pa.strip_file(dst / name):
                problems.append(f"{g['id']}/{name}: C2PA was still present, stripped")
            images.append(name)
        (dst / "post.md").write_text(post_md(g, images, order_of(g["id"])), encoding="utf-8")
        print(f"packaged {g['id']}  title {len(g['title'])}字  body {len(body)}字")
    for p in problems:
        print("WARN", p)
