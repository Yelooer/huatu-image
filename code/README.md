# 生成代码

这里是生成「瑶」组图用的脚本和配置，发布时不需要看这个目录。

- `scripts/`：生成、质检、打包脚本（主流程：make_month.py → run_month.py → qc_month.py → build_posts.py）
- `character/`：人物档案 yao.json 和脸部设定图
- `groups/`：每批的组配置，month01/ 是按系列写的整月配置

API key 不在仓库里。脚本从本地 `D:\xhs\image.txt` 读取 key（以 `sk-` 开头的那一行），自己用时需要在本地建这个文件。
