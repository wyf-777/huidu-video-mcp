# 上游原始说明存档

> 来源：GROOVIN / Zeto 公开分享的 `GROOVIN DEPTH CONVERTER`。  
> 存档目的：保留来源、作者信息和原始使用说明。  
> 注意：公开下载不等于取得商业再分发授权。

# GROOVIN DEPTH CONVERTER

ダンス動画などを**深度マップ動画**に変換するツールです。  
Seedance / Kling / Hailuo などのAI動画生成のモーションリファレンスに使えます。

by GROOVIN (zetogroovin.com)

---

## 必要なもの

- Python 3.9以上
- ネット接続（初回のみ、AIモデルを自動ダウンロード）

GPUは無くても動きます。NVIDIA GPU / M系Macがあれば自動で高速化されます。

## セットアップ

```text
pip install gradio opencv-python torch transformers pillow numpy
```

## 起動

```text
python groovin_depth_converter.py
```

ブラウザで `http://127.0.0.1:7860` を開き、動画をアップロードして変換を開始します。

## 原始推荐设置

| 项目 | 原始建议 |
|---|---|
| 模型 | Small |
| 输出分辨率 | 720p |
| 防闪烁 | 开启 |
| 保留音频 | 需要 FFmpeg |

## 原始免责声明

変換する動画の権利にはご注意ください。本ツールの利用による問題について作者は責任を負いません。

## 本地修改摘要

- 补充缺失的 `torchvision` 依赖。
- 中文化界面、错误和进度提示。
- 未检测到 FFmpeg 时默认关闭保留音频。
- 增加 Windows 双击启动文件。
- 启动后自动打开浏览器。

完整变更见项目根目录的 `CHANGELOG.md`。
