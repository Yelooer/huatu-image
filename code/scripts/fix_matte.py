"""One-off: rewrite glossy/oily makeup wording to a dry, matte Chinese-style finish."""
import json
import pathlib

CHAR = pathlib.Path(r"D:\xhs\character\yao.json")
BATCH = pathlib.Path(r"D:\xhs\groups\batch01.json")

MATTE_FULL = ("精致的中式全妆，妆面干净干爽：雾面奶油肌底妆，定过妆，整张脸是干爽细腻的哑光质感，"
              "没有油光、没有反光、没有出油，但依然能看到真实的皮肤纹理和细小毛孔；浅棕色眉笔勾勒的柔和平眉；"
              "粉棕色哑光眼影晕染出深邃眼窝，眼尾微微拉长的棕色眼线；浓密且根根分明的睫毛；带少量细闪的卧蚕；"
              "蜜桃粉哑光腮红晕染在苹果肌；只在鼻梁和眉骨有极少量柔和的高光；蜜桃玫瑰色的丝绒雾面唇。")

char = json.loads(CHAR.read_text(encoding="utf-8"))
char["blocks"]["妆容"] = MATTE_FULL
char["blocks"]["画质"] = char["blocks"]["画质"].replace(
    "能看到真实的皮肤纹理", "脸部是干爽的哑光肤质，没有油光和反光，能看到真实的皮肤纹理")
char["short"]["妆发"] = "中式干爽全妆（定妆雾面底妆、粉棕眼影、根根分明的睫毛、卧蚕、哑光腮红、丝绒雾面唇）；黑茶色长发+八字刘海"
char["short"]["画质"] = "手机原相机直出，无美颜无滤镜，干爽哑光肤质无油光，真实皮肤纹理，竖构图3:4"
CHAR.write_text(json.dumps(char, ensure_ascii=False, indent=2), encoding="utf-8")

REPLACE = [
    ("；脸上和锁骨有一点细汗的光泽。", "；额头和锁骨有少量细小的汗珠，但整体肤质依然干爽哑光，没有油光。"),
    ("；润唇；脸上有细汗的光泽。", "；自然的淡唇色；额头有少量细小的汗珠，但整体肤质依然干爽哑光，没有油光。"),
    ("细汗光泽", "额头微微细汗"),
    ("，有一点湿润的光泽。", "。"),
    ("修容和高光更明显", "修容更明显，只有极少量柔和的高光，整张脸干爽哑光、没有油光"),
    ("高光明显", "只有少量高光，肤质干爽哑光、没有油光"),
    ("雾面奶油肌底妆，但依然能看到", "雾面奶油肌底妆，定过妆，整张脸干爽哑光、没有油光和反光，但依然能看到"),
    ("雾面奶油肌底妆保留真实皮肤纹理", "定过妆的干爽雾面底妆，没有油光，保留真实皮肤纹理"),
    ("饱满水润的蜜桃玫瑰色玻璃唇釉", "蜜桃玫瑰色的丝绒雾面唇"),
    ("蜜桃玫瑰色水光唇釉", "蜜桃玫瑰色丝绒雾面唇"),
    ("水光唇釉", "丝绒雾面唇"),
    ("轻薄底妆，能看到", "轻薄干爽的哑光底妆，没有油光，能看到"),
    ("蜜桃色润唇", "蜜桃色雾面唇"),
    ("樱花粉色润唇", "樱花粉色雾面唇"),
]
text = BATCH.read_text(encoding="utf-8")
for old, new in REPLACE:
    n = text.count(old)
    text = text.replace(old, new)
    print(f"{n:>2}x  {old}")
json.loads(text)  # still valid JSON
BATCH.write_text(text, encoding="utf-8")
