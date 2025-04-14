import sys
import pkg_resources

# 讀取 requirements.txt
with open("requirements.txt", encoding="utf-8") as f:
    lines = []
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("    "):
            continue
        lines.append(line)

# 加入 torch 檢查條件
mode = 0  # 這行也可從環境變數取得
if mode == 0:
    lines.append("torch==2.6.0+cu118")

# 檢查未安裝或版本不符的套件
missing_or_mismatch = []

for req_str in lines:
    try:
        req = pkg_resources.Requirement.parse(req_str)
        pkg_resources.require(str(req))
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
        missing_or_mismatch.append(req_str)

# 回傳 1 代表需要安裝
sys.exit(1 if missing_or_mismatch else 0)
