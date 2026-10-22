"""Gradio adapter for the local prototype."""

import gradio as gr
import sys

from .constants import MODEL_LABELS, RESOLUTION_LABELS
from .converter import ConversionOptions, DepthVideoConverter, ProgressUpdate
from .errors import ConversionError
from .media import ffmpeg_available
from .ui_localization import LOCALIZE_JS
from .ai_connection import app_options
from .ai_settings_ui import add_ai_settings

CSS = """
body, .gradio-container { background: #0a0a0a !important; }
.gradio-container { font-family: 'Helvetica Neue', sans-serif; }
#title { color: #fff; font-weight: 900; letter-spacing: 0.15em; }
#subtitle { color: #888; letter-spacing: 0.3em; font-size: 12px; }
"""

GRADIO_PROGRESS = gr.Progress()


def build_app(converter: DepthVideoConverter | None = None) -> gr.Blocks:
    service = converter or DepthVideoConverter()

    def convert_from_ui(
        video_path: str | None,
        model_label: str,
        resolution_label: str,
        invert: bool,
        keep_audio: bool,
        smooth_normalization: bool,
        progress: gr.Progress = GRADIO_PROGRESS,
    ) -> tuple[str, str]:
        """将视频转换为相对深度图视频，返回输出文件和处理状态。

        Args:
            video_path: 上传后的视频文件。MCP 客户端应提供可访问的视频 URL。
            model_label: 模型档位，Small 速度较快，Base 和 Large 需要更多资源。
            resolution_label: 输出分辨率预设；720p 按长边 1280 像素缩放，保留比例。
            invert: 是否反转深度图的黑白方向。
            keep_audio: 是否保留原音频，需要 FFmpeg。
            smooth_normalization: 是否启用时间平滑，减少闪烁。
        """
        if not video_path:
            raise gr.Error("请先上传视频")

        def report(update: ProgressUpdate) -> None:
            total = update.total_frames if update.total_frames > 0 else "未知"
            progress(
                update.ratio,
                desc=(f"正在转换 {update.completed_frames}/{total} 帧（{update.device.upper()}）"),
            )

        options = ConversionOptions(
            model_name=MODEL_LABELS[model_label],
            resolution=RESOLUTION_LABELS[resolution_label],
            invert=invert,
            keep_audio=keep_audio,
            smooth_normalization=smooth_normalization,
        )
        try:
            result = service.convert(video_path, options, progress_callback=report)
        except ConversionError as exc:
            raise gr.Error(str(exc)) from exc

        status = (
            f"✅ 转换完成 | {result.processed_frames}帧 / {result.fps:.1f}fps / "
            f"{result.width}x{result.height} / 计算设备：{result.device.upper()}"
        )
        if result.warnings:
            status += "\n⚠️ " + "；".join(result.warnings)
        return str(result.output_path), status

    with gr.Blocks(title="深度视频转换器") as app:
        gr.HTML(
            '<h1 id="title">深度视频转换器</h1>'
            '<p id="subtitle">普通视频 → 深度图视频 · AI 动作参考</p>'
        )

        with gr.Row():
            with gr.Column():
                video_input = gr.Video(label="输入视频（舞蹈视频等）")
                model_input = gr.Dropdown(
                    choices=list(MODEL_LABELS),
                    value="Small（高速，推荐）",
                    label="深度模型",
                )
                resolution_input = gr.Dropdown(
                    choices=list(RESOLUTION_LABELS),
                    value="720p（长边1280）",
                    label="输出分辨率（越小越快）",
                )
                with gr.Row():
                    invert_input = gr.Checkbox(label="黑白反转（近处显示为黑色）")
                    audio_input = gr.Checkbox(
                        label="保留音频（需要FFmpeg）",
                        value=ffmpeg_available(),
                    )
                    smoothing_input = gr.Checkbox(label="防止闪烁（时间平滑）", value=True)
                run_button = gr.Button("开始转换", variant="primary")
            with gr.Column():
                video_output = gr.Video(label="深度图视频")
                status_output = gr.Textbox(label="处理状态", interactive=False)

        run_button.click(
            convert_from_ui,
            inputs=[
                video_input,
                model_input,
                resolution_input,
                invert_input,
                audio_input,
                smoothing_input,
            ],
            outputs=[video_output, status_output],
            concurrency_limit=1,
        )
        add_ai_settings()
    return app


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    app = build_app()
    print("[DEPTH VIDEO CONVERTER] 本地页面：http://127.0.0.1:7860/")
    if not ffmpeg_available():
        print("提示：未找到FFmpeg，保留音频功能将不可用。")
    app.launch(
        inbrowser=True, css=CSS, theme=gr.themes.Monochrome(),
        js=LOCALIZE_JS, footer_links=["api", "settings"],
        mcp_server=True, server_name="127.0.0.1", server_port=7860,
        app_kwargs=app_options(),
    )


if __name__ == "__main__":
    main()
