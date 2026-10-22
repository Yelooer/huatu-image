"""Quality check for a big batch.

1. Completeness: every group has 5 shots (01..05) and its cover candidates.
(A Haar-cascade "two faces" check was tried and dropped: on full-body shots it fires on fabric and knees,
so extra people are checked by eye on the review sheets.)
2. Review sheets: one row per group = 5 shots + cover candidates, ROWS groups per JPEG,
   saved as _review/<prefix>_NN.jpg; cover candidates are labelled c1, c2, c3.
3. Face sheets: shot 4 (the close-up) of each group, face cropped at native resolution, 15 per JPEG,
   for checking skin shine.
Usage: python qc_month.py <batch.json> <prefix> [group_id ...]
"""
import json
import sys
import pathlib
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import face_crops

OUT = pathlib.Path(r"D:\xhs\output")
REVIEW = OUT / "_review"
H, ROWS, FACES_PER_SHEET, CELL = 360, 3, 15, 300
FONT = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 26)


def shots_of(gid):
    return sorted((OUT / gid).glob("0*.png"))


def covers_of(gid):
    return sorted((OUT / gid / "_covers").glob("c*.png"))


def row(gid, title):
    paths = shots_of(gid) + covers_of(gid)
    labels = [p.name[:2] for p in shots_of(gid)] + [p.name[:2] for p in covers_of(gid)]
    imgs = [Image.open(p).convert("RGB") for p in paths]
    imgs = [im.resize((round(im.width * H / im.height), H)) for im in imgs]
    r = Image.new("RGB", (sum(i.width for i in imgs) + 6 * len(imgs) + 20, H + 40), "white")
    d = ImageDraw.Draw(r)
    d.text((6, 4), f"{gid}  {title}", fill="black", font=FONT)
    x = 0
    for k, (im, lab) in enumerate(zip(imgs, labels)):
        if k == 5:
            x += 20  # gap before the cover candidates
        r.paste(im, (x, 40))
        d.text((x + 6, 44), lab, fill="red", font=FONT, stroke_width=2, stroke_fill="white")
        x += im.width + 6
    return r


def stack(rows, out):
    sheet = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows) + 10 * len(rows)), "white")
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height + 10
    sheet.save(out, quality=85)


if __name__ == "__main__":
    groups = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    prefix = sys.argv[2]
    wanted = set(sys.argv[3:])
    if wanted:
        groups = [g for g in groups if g["id"] in wanted]
    REVIEW.mkdir(exist_ok=True)

    ok = []
    for g in groups:
        gid = g["id"]
        n, c = len(shots_of(gid)), len(covers_of(gid))
        if n < 5:
            print(f"INCOMPLETE {gid}: {n}/5 shots, {c} covers")
            continue
        ok.append(g)

    for i in range(0, len(ok), ROWS):
        stack([row(g["id"], g["title"]) for g in ok[i:i + ROWS]], REVIEW / f"{prefix}_{i // ROWS + 1:03d}.jpg")

    crops = []
    for g in ok:
        p = shots_of(g["id"])[3]
        box = face_crops.largest_face(p)
        if box:
            c = Image.open(p).convert("RGB").crop(box)
            c.thumbnail((CELL, CELL))
            ImageDraw.Draw(c).text((4, 2), g["id"][:4], fill="red", font=FONT, stroke_width=2, stroke_fill="white")
            crops.append(c)
    for i in range(0, len(crops), FACES_PER_SHEET):
        part = crops[i:i + FACES_PER_SHEET]
        sheet = Image.new("RGB", (5 * (CELL + 4), ((len(part) + 4) // 5) * (CELL + 4)), "white")
        for k, c in enumerate(part):
            sheet.paste(c, ((k % 5) * (CELL + 4), (k // 5) * (CELL + 4)))
        sheet.save(REVIEW / f"{prefix}_faces_{i // FACES_PER_SHEET + 1:02d}.jpg", quality=90)
    print(f"{len(ok)}/{len(groups)} complete; review sheets -> {REVIEW}\\{prefix}_*.jpg")
