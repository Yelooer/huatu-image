"""Probe the image APIs: list models available on the proxy."""
import pathlib
import requests

lines = [l.strip() for l in pathlib.Path(r"D:\xhs\image.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
KEY = next(l for l in lines if l.startswith("sk-"))
BASE = "https://api-cn.rolldek.com"

r = requests.get(f"{BASE}/v1/models", headers={"Authorization": f"Bearer {KEY}"}, timeout=30)
print("v1/models", r.status_code)
try:
    ids = [m["id"] for m in r.json().get("data", [])]
    print([i for i in ids if any(k in i.lower() for k in ("image", "banana", "gemini", "gpt"))])
except Exception:
    print(r.text[:500])
