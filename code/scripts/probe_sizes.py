"""Find which size / quality values gpt-image-2-high accepts (invalid values should error without billing)."""
import sys
import pathlib
import requests

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import imgapi

r = requests.post(f"{imgapi.BASE}/v1/images/generations", headers={"Authorization": f"Bearer {imgapi.KEY}"},
                  json={"model": imgapi.GPT_MODEL, "prompt": "test", "size": "9999x9999", "quality": "high", "n": 1},
                  timeout=120)
print(r.status_code, r.text[:1500])
