"""Crop the largest face from each image at native resolution into one review grid (for checking skin shine).

Usage: python face_crops.py <out.jpg> <image or folder> [...]
Faces are found with OpenCV's Haar cascade; images where no face is found are listed and skipped.
"""
import sys
import pathlib
import cv2
import numpy as np
from PIL import Image

CELL = 360   # each crop is shown at this size; crops are taken at native resolution then scaled to fit
COLS = 5
CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def largest_face(path):
    # cv2.imread can't open non-ASCII paths on Windows, so decode with PIL
    gray = np.array(Image.open(path).convert("L"))
    faces = CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(90, 90))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    pad = int(w * 0.35)  # include forehead, cheeks and chin
    H, W = gray.shape
    return (max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + pad))


def iter_images(targets):
    for t in map(pathlib.Path, targets):
        if t.is_dir():
            yield from sorted(t.rglob("0*.png"))
        else:
            yield t


if __name__ == "__main__":
    out, targets = sys.argv[1], sys.argv[2:]
    crops, missed = [], []
    for p in iter_images(targets):
        box = largest_face(p)
        if box is None:
            missed.append(p)
            continue
        crop = Image.open(p).convert("RGB").crop(box)
        crop.thumbnail((CELL, CELL))
        crops.append(crop)
    rows = (len(crops) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * (CELL + 6), max(1, rows) * (CELL + 6)), "white")
    for i, c in enumerate(crops):
        sheet.paste(c, ((i % COLS) * (CELL + 6), (i // COLS) * (CELL + 6)))
    sheet.save(out, quality=92)
    print(f"{len(crops)} faces -> {out}")
    for p in missed:
        print("no face:", p)
