"""Generate the same 'Yao' base portrait on both models for a face-quality comparison."""
import sys
import time
import pathlib
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import imgapi

OUT = pathlib.Path(r"D:\xhs\test")
OUT.mkdir(exist_ok=True)

PROMPT = (
    "A candid, photorealistic smartphone photo of a 22-year-old Chinese woman named Yao. "
    "Natural, girl-next-door look, not an influencer face: softly rounded oval face with a slightly "
    "fuller lower cheek, gentle double eyelids with medium-sized almond eyes (not oversized), "
    "a small low nose bridge with a soft rounded tip, naturally full lips, a faint mole under her left eye, "
    "subtle facial asymmetry, visible skin texture and pores, a little natural redness on the cheeks, "
    "fine baby hairs at the hairline. Shoulder-length dark brown hair with loose strands. "
    "Light everyday makeup. She wears a plain white t-shirt. Head-and-shoulders, facing the camera with a "
    "relaxed, slight smile, standing by a window in soft daylight, plain light wall behind her. "
    "Shot on an iPhone, slight grain, true-to-life colors, no beauty filter, no skin smoothing, no retouching."
)

jobs = {
    "gpt": lambda: imgapi.gpt(PROMPT, size="1024x1536"),
    "gemini": lambda: imgapi.gemini(PROMPT, ratio="3:4", image_size="2K"),
}


def run(name):
    t = time.time()
    try:
        data = jobs[name]()
        path = OUT / f"base_{name}.png"
        path.write_bytes(data)
        return f"{name}: ok {len(data)//1024}KB in {time.time()-t:.0f}s -> {path}"
    except Exception as e:
        return f"{name}: FAILED in {time.time()-t:.0f}s: {e}"


with ThreadPoolExecutor(2) as ex:
    for line in ex.map(run, jobs):
        print(line)
