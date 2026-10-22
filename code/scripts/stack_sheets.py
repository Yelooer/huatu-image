"""Stack several groups' contact sheets vertically (with the group id written on each row) for faster review.

Usage: python stack_sheets.py <out.jpg> <group_id> [...]
"""
import sys
import pathlib
from PIL import Image, ImageDraw, ImageFont

REVIEW = pathlib.Path(r"D:\xhs\output\_review")

if __name__ == "__main__":
    out, ids = sys.argv[1], sys.argv[2:]
    rows = [Image.open(REVIEW / f"{gid}.jpg") for gid in ids]
    W = max(r.width for r in rows)
    sheet = Image.new("RGB", (W, sum(r.height + 6 for r in rows)), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("msyh.ttc", 44)
    except OSError:
        font = ImageFont.load_default()
    y = 0
    for gid, r in zip(ids, rows):
        sheet.paste(r, (0, y))
        draw.rectangle((0, y, 520, y + 60), fill="black")
        draw.text((10, y + 4), gid, fill="yellow", font=font)
        y += r.height + 6
    sheet.save(out, quality=88)
    print(out)
