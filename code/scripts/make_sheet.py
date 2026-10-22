"""Generate the character face sheet (front / 3-4 / profile headshots) that every group references."""
import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import imgapi

char = json.loads(pathlib.Path(r"D:\xhs\character\yao.json").read_text(encoding="utf-8"))
b = char["blocks"]

PROMPT = (
    "一张真人摄影的人物脸部设定图，横版构图，同一个女生的三张肩部以上照片从左到右并排："
    "左边是正脸看镜头，中间是45度侧脸，右边是纯侧脸。三张是同一个人、同一妆容、同一发型、同样的光线，"
    "浅灰色纯色背景，柔和的自然窗光，像真实模特的试妆定妆照，清晰展示五官、妆容细节、发色和耳饰。"
    "她穿着简单的白色细肩带背心，表情自然放松，嘴角带一点笑。\n"
    + "\n".join(f"【{k}】{b[k]}" for k in ["主体", "五官", "妆容", "发型", "饰品"])
    + "\n【画质】相机原图直出，没有美颜、滤镜和精修：脸部是定过妆的干爽哑光肤质，额头、鼻子和脸颊都没有油光和反光；"
      "清楚看到真实的皮肤纹理、毛孔、细小瑕疵、细小的汗毛和自然的面部阴影，妆容是真实化妆品的质感，"
      "不是光滑的塑料皮肤，不是CG，高清。"
)

if __name__ == "__main__":
    out = pathlib.Path(char["sheet"])
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():  # keep every previous sheet as yao_sheet_v1.png, _v2.png, ...
        n = 1
        while (backup := out.with_name(f"{out.stem}_v{n}{out.suffix}")).exists():
            n += 1
        out.rename(backup)
        print("previous sheet ->", backup)
    out.write_bytes(imgapi.gpt25(PROMPT, size="2048x1536"))
    print("ok ->", out)
