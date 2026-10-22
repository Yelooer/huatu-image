"""Round 2: (a) prettier-but-real base face, (b) face retention from a reference into a cosplay shot."""
import sys
import time
import pathlib
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import imgapi

OUT = pathlib.Path(r"D:\xhs\test")

PRETTY = (
    "A photorealistic smartphone selfie-style portrait of a pretty 21-year-old Chinese woman, the kind of "
    "naturally attractive girl you would see as a popular cosplayer on Xiaohongshu, but clearly a real person, "
    "not an AI influencer face. Soft oval face with a gently rounded chin, clear bright almond eyes with natural "
    "double eyelids (not oversized), slightly straight natural brows, small soft nose, naturally plump lips with a "
    "light rosy tint, a tiny mole under her left eye, very subtle asymmetry. Fair skin with real texture: faint "
    "pores on the nose and cheeks, a little natural blush, fine baby hairs at the hairline. Light, clean everyday "
    "makeup (soft brown eyeliner, light lip tint). Long dark brown hair with soft loose strands. Plain white "
    "t-shirt. Head-and-shoulders, facing camera, gentle closed-mouth smile, soft window daylight, plain light wall. "
    "Shot on iPhone, natural colors, slight grain. No heavy beauty filter, no plastic smooth skin, no CGI look."
)

COS = (
    "Use the woman in the reference image as the exact same person: keep her face shape, eyes, nose, lips, "
    "mole under the left eye, and skin texture identical. She is now cosplaying Hatsune Miku at a crowded anime "
    "convention hall: long teal twin-tail wig, grey sleeveless top with teal tie, black pleated skirt, detached "
    "sleeves, headset. Waist-up candid photo, she is looking at the camera with a small smile and holding a teal "
    "glow stick. Convention booths and people blurred in the background, mixed indoor ceiling lighting. "
    "Shot on iPhone, realistic photo, natural skin texture, slight grain, no beauty filter."
)

jobs = {
    "pretty_gpt": lambda: imgapi.gpt(PRETTY, size="1024x1536"),
    "pretty_gemini": lambda: imgapi.gemini(PRETTY, ratio="3:4", image_size="2K"),
    "cos_gpt": lambda: imgapi.gpt(COS, refs=[str(OUT / "base_gpt.png")], size="1024x1536"),
    "cos_gemini": lambda: imgapi.gemini(COS, refs=[str(OUT / "base_gemini.png")], ratio="3:4", image_size="2K"),
}


def run(name):
    t = time.time()
    try:
        data = jobs[name]()
        path = OUT / f"{name}.png"
        path.write_bytes(data)
        return f"{name}: ok in {time.time()-t:.0f}s -> {path}"
    except Exception as e:
        return f"{name}: FAILED in {time.time()-t:.0f}s: {e}"


if __name__ == "__main__":
    names = sys.argv[1:] or list(jobs)
    with ThreadPoolExecutor(len(names)) as ex:
        for line in ex.map(run, names):
            print(line)
