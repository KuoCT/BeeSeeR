## Nuitka 參數表格
| 參數                                                                                          | 說明 |
|-----------------------------------------------------------------------------------------------|------|
| `--standalone`                                                                                | 打包成獨立可執行檔 |
| `--enable-plugin=tk-inter`                                                                    | 啟用 tkinter GUI 支援 |
| `--include-distribution-metadata=Pillow`                                                      | 包含 Pillow metadata，避免 PIL 運作問題 |

### Transformers 相關
| 參數                                                                                          | 說明 |
|-----------------------------------------------------------------------------------------------|------|
| `--include-package=transformers.models.vit`                                                   | 僅包含 ViT 模型（MangaOCR 使用） |
<!-- | `--include-package=transformers.models.vision_encoder_decoder`                                | *(可選)* 若有缺失，加入視覺編碼器解碼器 |
| `--include-package=transformers.image_processing_vit`                                         | *(可選)* 若有缺失，加入 ViT 圖像處理器 |
| `--include-package=transformers.tokenization_auto`                                            | *(可選)* 若有缺失，加入自動 tokenizer |
| `--nofollow-import-to=transformers.models.bert`                                               | 排除 BERT 模型 |
| `--nofollow-import-to=transformers.models.gpt2`                                               | 排除 GPT2 模型 |
| `--nofollow-import-to=transformers.models.t5`                                                 | 排除 T5 模型 |
| `--nofollow-import-to=transformers.models.roberta`                                            | 排除 Roberta 模型 |
| `--nofollow-import-to=transformers.models.gpt_neo`                                            | 排除 GPT-Neo 模型 |
| `--nofollow-import-to=transformers.models.llama`                                              | 排除 LLaMA 模型 |
| `--nofollow-import-to=transformers.models.bloom`                                              | 排除 Bloom 模型 |
| `--nofollow-import-to=transformers.models.clip`                                               | 排除 CLIP 模型 |
| `--nofollow-import-to=transformers.models.wav2vec2`                                           | 排除 Wav2Vec2 語音模型 |
| `--nofollow-import-to=transformers.models.whisper`                                            | 排除 Whisper 語音模型 |
| `--nofollow-import-to=transformers.models.beit`                                               | 排除 BEiT 圖像模型 |
| `--nofollow-import-to=transformers.models.segformer`                                          | 排除 SegFormer 圖像分割模型 |
| `--nofollow-import-to=transformers.models.dinov2`                                             | 排除 DINOv2 圖像模型 |
| `--nofollow-import-to=transformers.models.deit`                                               | 排除 DeiT 圖像模型 | -->

### PyTorch 相關
| 參數                                                                                          | 說明 |
|-----------------------------------------------------------------------------------------------|------|
<!-- | `--nofollow-import-to=torchvision`                                                            | 排除 torchvision，圖像資料處理套件（訓練用） |
| `--nofollow-import-to=torchaudio`                                                             | 排除 torchaudio，音訊資料處理套件（訓練用） |
| `--nofollow-import-to=torchtext`                                                              | 排除 torchtext，NLP 資料集與前處理（訓練用） |
| `--nofollow-import-to=torch.optim`                                                            | 排除優化器模組（訓練用） |
| `--nofollow-import-to=torch.onnx`                                                             | 排除 ONNX 轉換模組（訓練用） | 
| `--nofollow-import-to=torch.nn.parallel`                                                      | 排除 DataParallel，多 GPU 訓練工具（訓練用）(排除後會報錯) |
| `--nofollow-import-to=torch.distributed`                                                      | 排除分散式訓練模組（訓練用）(排除後會報錯) |
| `--nofollow-import-to=torch.cuda.amp`                                                         | 排除混合精度訓練（訓練用）(排除後會報錯) |-->
| `--module-parameter=torch-disable-jit=yes`                                                    | 禁用 JIT / TorchScript（若不使用 JIT 可省略） |

### 資料夾與資源
| 參數                                                                                          | 說明 |
|-----------------------------------------------------------------------------------------------|------|
| `--include-data-dir=./env/Lib/site-packages/manga_ocr/assets=./manga_ocr/assets`              | 包含 manga_ocr 的資源檔案 |
| `--include-data-files=./env/Lib/site-packages/unidic_lite/dicdir\**\*=./unidic_lite/dicdir/`  | 包含 unidic_lite 辭典資料 |
| `--include-data-dir=./checkpoint=./checkpoint`                                                | 包含 checkpoint 資料夾 |
| `--include-data-dir=./icon=./icon`                                                            | 包含 icon 資料夾 |
| `--include-data-dir=./persona=./persona`                                                      | 包含 persona 資料夾 |
| `--include-data-dir=./theme=./theme`                                                          | 包含 theme 資料夾 |

### 輸出設定
| 參數                                                                                          | 說明 |
|-----------------------------------------------------------------------------------------------|------|
| `--output-dir=build`                                                                          | 輸出資料夾為 build |
| `--windows-icon-from-ico=./icon/logo_dark.ico`                                                | 設定 exe 檔案 icon |
| `--windows-console-mode=hide`                                                                 | 隱藏命令提示字元 |
| `--output-filename=BeeSeeR.exe`                                                               | 設定輸出的 exe 名稱 |
| `GUI.py`                                                                                      | 主程式檔案 |