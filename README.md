# 深度视频转换器 · 中文 MCP 版

将普通视频转换为相对深度图视频，供视频创作和动作参考使用。提供中文网页、Windows 图形启动器、命令行和带连接密钥的 MCP 接口。

本版本从 `wyf-777/huidu-video` 的早期提交 `df5fc206cc15e23c5ff97bd394b27322472c29db` 衍生，包含后续中文化和 MCP 改进；不是未经修改的原始快照。

## 功能

- Depth Anything V2 Small、Base、Large 模型；自动选择 CUDA、Apple MPS 或 CPU。
- 保持视频比例与帧率，提供分辨率预设、深度反转和时间平滑防闪烁。
- 720p 预设表示长边最多 1280 像素，竖屏等比例缩放。
- 安装 FFmpeg 后可保留音频并转为 H.264；没有 FFmpeg 时仍可生成无音频 MP4，兼容性取决于播放器。
- 中文网页及设置、API/MCP 文档说明。
- Windows 图形启动器自动打开网页，提供日志和停止服务入口。
- MCP 支持 Streamable HTTP；STDIO 客户端可通过 `mcp-remote` 转接。
- 在“设置 → AI 连接”开启、测试连接、复制配置和重新生成密钥。

## 首次安装

需要 Python 3.11–3.13。推荐先使用 Small 模型验证；首次转换会从 Hugging Face 下载模型，需要网络和足够的磁盘空间。模型权重、虚拟环境和用户视频不包含在仓库中。

在项目目录打开 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

需要 NVIDIA 加速时，请按 PyTorch 官方说明安装与驱动兼容的 CUDA 版本。FFmpeg 是可选系统依赖，需要放入 PATH。

## 打开网页

Windows 安装后双击 `启动图形界面.cmd`。启动器会自动打开 <http://127.0.0.1:7860/>，使用期间保留启动器窗口，关闭由它启动的服务会中断正在进行的转换。

也可以双击 `启动深度转换器.cmd` 使用控制台启动，或运行：

```powershell
.\.venv\Scripts\python.exe -X utf8 groovin_depth_converter.py
```

macOS / Linux 可在虚拟环境中执行 `pip install -r requirements.txt`，再运行 `python groovin_depth_converter.py`；Windows 图形启动器仅适用于 Windows。

上传视频后，选择模型和输出分辨率，按需开启防闪烁和保留音频，然后开始转换并下载结果。

## 连接 AI / MCP

1. 打开网页“设置 → AI 连接（MCP）”，开启连接。
2. 点击“测试连接”，然后“复制连接配置”。
3. 把完整配置添加到支持 MCP 的 AI 客户端。上传本地文件时，使用文档中的 Gradio 上传工具或先手动上传。

Streamable HTTP 配置格式如下，实际密钥以网页复制的配置为准：

```json
{
  "mcpServers": {
    "depth-video": {
      "url": "http://127.0.0.1:7860/gradio_api/mcp/",
      "headers": { "Authorization": "Bearer <你的连接密钥>" }
    }
  }
}
```

只支持 STDIO 的客户端需要额外安装 Node.js，并使用以下转接配置；首次执行 `npx` 需要网络：

```json
{
  "mcpServers": {
    "depth-video": {
      "command": "npx",
      "args": [
        "--yes", "mcp-remote",
        "http://127.0.0.1:7860/gradio_api/mcp/",
        "--transport", "http-only",
        "--header", "Authorization: Bearer <你的连接密钥>"
      ]
    }
  }
}
```

Windows 客户端若不能直接调用 `npx`，可按该客户端要求使用 `npx.cmd`。可选的 `upload_files_to_gradio` 上传助手需要另装 `uv`；详细配置见网页 MCP 文档。

工具 `convert_from_ui` 接收六项参数：`video_path`、`model_label`、`resolution_label`、`invert`、`keep_audio`、`smooth_normalization`，返回输出文件和处理状态。模型标签需使用工具描述中列出的完整选项。

连接默认关闭。同一服务共用一把密钥，尚未实现网站用户账户或每人独立密钥。Windows 配置保存在当前系统用户的 `%LOCALAPPDATA%\DepthVideoConverter\ai-connection.json`；不要分享或提交此文件。重新生成密钥后，客户端需要更新配置。

文档“复制页面”包含密钥占位符，可用于分享说明；“复制连接配置”包含真实密钥，应妥善保管。

## 命令行转换

```powershell
.\.venv\Scripts\depth-video.exe input.mp4 output.mp4 --model small --resolution 720p
.\.venv\Scripts\depth-video.exe --help
```

默认开启时间平滑且不保留音频；可用 `--no-smoothing` 关闭平滑，`--keep-audio` 保留音频。

## 验证

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

已通过 HTTP 和 STDIO 进行实际上传、MCP 调用、视频下载与解码验证：Small、720p、防闪烁开启、无音频；输出为 1280×720、8 帧、8 fps。另覆盖无密钥、错误密钥、关闭连接、密钥轮换及本地上传路径校验。测试使用合成视频，用户视频和运行密钥未随代码发布。

## 当前范围

这是本机工具，默认仅监听 `127.0.0.1:7860`。其他电脑不能直接访问这个地址。MCP 密钥只保护 MCP 调用，网页、上传和普通 Gradio API 没有完整的用户认证；管理界面可以显示服务密钥，不能据此直接作为公网多用户服务部署。

还没有账户、计费、租户隔离或持久化任务队列。`docs/` 中的商业化、部署及任务架构文档包含未来设计，不代表这些功能已经实现。

## 来源与许可

本项目基于 GROOVIN / Zeto 分享的 `GROOVIN DEPTH CONVERTER` 修改，作者及原始说明见 [上游说明](docs/UPSTREAM_README.md)。原项目文档记载负责人已确认取得许可；本仓库未附授权原件，也未新增统一的开源许可证。公开可见不代表授予任意复制、再分发或商业使用的权利，相关使用须核实授权范围。

模型权重和依赖遵循各自许可证：Depth Anything V2 Small 模型卡标注 Apache-2.0，Base 和 Large 模型卡标注 CC-BY-NC-4.0；使用前请核实具体模型版本和适用范围。用户应拥有输入视频及相关内容所需的权利。

其他文档：[开发指南](docs/DEVELOPMENT.md) · [授权检查](docs/LICENSING_COMMERCIALIZATION.md) · [变更记录](CHANGELOG.md)。
