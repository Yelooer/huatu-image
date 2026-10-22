"""Thin client for the two image models behind the rolldek proxy.

gpt(prompt, refs=None, size=...)      -> bytes (PNG/JPEG)
gpt25(prompt, refs=None, size=...)    -> bytes, gpt-image-2.5 (max 2K)
gemini(prompt, refs=None, ratio=..., image_size=...) -> bytes
"""
import base64
import pathlib
import requests

_lines = [l.strip() for l in pathlib.Path(r"D:\xhs\image.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
KEY = next(l for l in _lines if l.startswith("sk-"))
BASE = "https://rolldek.com"
GPT_MODEL = "gpt-image-2-high"
GEMINI_MODEL = "gemini-nano-banana-2.1"
TIMEOUT = 600


def _ref_bytes(path, max_side=1536):
    """Downscale a reference image to a JPEG so uploads stay small; face identity survives fine at this size."""
    import io
    from PIL import Image
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=92)
    return buf.getvalue()


def _fetch_image(item):
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    if item.get("url"):
        return requests.get(item["url"], timeout=TIMEOUT).content
    raise RuntimeError(f"no image in item: {str(item)[:300]}")


def gpt(prompt, refs=None, size="2880x3840", quality="high", model=GPT_MODEL):
    headers = {"Authorization": f"Bearer {KEY}"}
    params = {"model": model, "prompt": prompt, "size": size, "quality": quality, "n": 1}
    if refs:
        files = [("image[]", (pathlib.Path(p).stem + ".jpg", _ref_bytes(p), "image/jpeg")) for p in refs]
        r = requests.post(f"{BASE}/v1/images/edits", headers=headers, timeout=TIMEOUT, data=params, files=files)
    else:
        r = requests.post(f"{BASE}/v1/images/generations", headers=headers, timeout=TIMEOUT, json=params)
    if r.status_code != 200:
        raise RuntimeError(f"gpt {r.status_code}: {r.text[:500]}")
    return _fetch_image(r.json()["data"][0])


def gpt25(prompt, refs=None, size="1536x2048", quality="high"):
    """gpt-image-2.5 tops out at 2K."""
    return gpt(prompt, refs=refs, size=size, quality=quality, model="gpt-image-2.5")


def gemini(prompt, refs=None, ratio="3:4", image_size="4K"):
    parts = []
    for p in refs or []:
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(_ref_bytes(p)).decode()}})
    parts.append({"text": prompt})
    body = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"],
                             "imageConfig": {"aspectRatio": ratio, "imageSize": image_size}},
    }
    r = requests.post(f"{BASE}/v1beta/models/{GEMINI_MODEL}:generateContent", timeout=TIMEOUT,
                      headers={"x-goog-api-key": KEY, "Authorization": f"Bearer {KEY}"}, json=body)
    if r.status_code != 200:
        raise RuntimeError(f"gemini {r.status_code}: {r.text[:500]}")
    for cand in r.json().get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            data = part.get("inlineData") or part.get("inline_data")
            if data:
                return base64.b64decode(data["data"])
    raise RuntimeError(f"gemini returned no image: {r.text[:500]}")
