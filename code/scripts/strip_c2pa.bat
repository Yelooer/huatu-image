@echo off
chcp 65001 >nul
rem 把图片或文件夹拖到这个文件上即可清除 C2PA；双击则处理 D:\xhs\huatu-image\posts 全部图片
if "%~1"=="" (
    python "%~dp0strip_c2pa.py" "D:\xhs\huatu-image\posts"
) else (
    python "%~dp0strip_c2pa.py" %*
)
pause
