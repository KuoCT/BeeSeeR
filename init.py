import os
import argparse

# 解析命令列參數
parser = argparse.ArgumentParser(description="OCR 模型控制器")
parser.add_argument("--force-cpu", action="store_true", help="強制使用 CPU 模式")
args = parser.parse_args()

# 根據 `--force-cpu` 設置環境變數
if args.force_cpu:
    os.environ["CUDA_VISIBLE_DEVICES"] = ","  # 在 Windows 環境中要使用空列表 ","

import gc
from torch import cuda  # 在設置 CUDA_VISIBLE_DEVICES 之後載入 torch
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor

def download_models():
    """下載 OCR 模型並確保它們已被加載一次"""

    # 判斷裝置
    device = "CUDA" if cuda.is_available() else "CPU"
    print(f"\033[32m[INFO]正在下載並初始化 OCR 模型（使用裝置: {device}），請稍候...\033[0m")

    # 初始化一次，確保模型已下載
    recognition_predictor = RecognitionPredictor()
    detection_predictor = DetectionPredictor()

    # 釋放記憶體（CUDA 模式釋放 VRAM; CPU 模式釋放 DRAM）
    if cuda.is_available():
        del recognition_predictor
        del detection_predictor
        cuda.empty_cache()
        cuda.ipc_collect()
        print("\033[32m[INFO]已釋放 GPU 記憶體\033[0m")
    else:
        gc.collect()
        print("\033[32m[INFO]已釋放 CPU 記憶體\033[0m")

    print("\033[32m[INFO]OCR 模型下載完成！\033[0m")

if __name__ == "__main__":
    # 執行模型下載
    download_models()
