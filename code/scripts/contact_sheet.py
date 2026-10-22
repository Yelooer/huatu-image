"""Put a group's shots side by side in one JPEG for quick review; cover candidates go in a second row.

Usage: python contact_sheet.py <group_id> [...]   -> D:/xhs/output/_review/<group_id>.jpg
"""
import sys
import pathlib
from PIL import Image, ImageDraw, ImageFont

OUT_ROOT = pathlib.Path(r"D:\xhs\output")
REVIEW = OUT_ROOT / "_review"
H = 720
FONT = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 36)


def row(paths, labels):
    imgs = [Image.open(p).convert("RGB") for p in paths]
    imgs = [im.resize((round(im.width * H / im.height), H)) for im in imgs]
    r = Image.new("RGB", (sum(im.width for im in imgs) + 8 * (len(imgs) - 1), H), "white")
    d, x = ImageDraw.Draw(r), 0
    for im, lab in zip(imgs, labels):
        r.paste(im, (x, 0))
        d.text((x + 10, 6), lab, fill="red", font=FONT, stroke_width=2, stroke_fill="white")
        x += im.width + 8
    return r


if __name__ == "__main__":
    REVIEW.mkdir(exist_ok=True)
    for gid in sys.argv[1:]:
        shots = sorted((OUT_ROOT / gid).glob("0*.png"))
        rows = [row(shots, [p.name[:2] for p in shots])]
        covers = sorted((OUT_ROOT / gid / "_covers").glob("c*.png"))
        if covers:
            rows.append(row(covers, [f"候选{p.name[1]}" for p in covers]))
        sheet = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows) + 12 * (len(rows) - 1)), "white")
        y = 0
        for r in rows:
            sheet.paste(r, (0, y))
            y += r.height + 12
        out = REVIEW / f"{gid}.jpg"
        sheet.save(out, quality=88)
        print(out)
