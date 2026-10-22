"""Graphical controls for a user's local MCP connection."""

import json

import gradio as gr
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from .ai_connection import get_connection


def add_ai_settings():
    connection = get_connection()

    def values(request: gr.Request):
        base = str(request.request.base_url).rstrip("/")
        state = "已开启 · AI 助手可以连接" if connection.enabled else "已关闭 · 暂不接受 AI 调用"
        config = json.dumps(connection.client_config(base), ensure_ascii=False, indent=2)
        return state, base + "/gradio_api/mcp/", config

    def update(enabled: bool, request: gr.Request):
        connection.set_enabled(enabled)
        return values(request)

    def rotate(request: gr.Request):
        connection.rotate_token()
        return (*values(request), "已生成新密钥，请在 AI 客户端更新连接配置。")

    async def test(request: gr.Request):
        if not connection.enabled:
            return "请先打开“允许 AI 助手连接”，再测试。"
        base = str(request.request.base_url).rstrip("/")
        try:
            async with httpx.AsyncClient(trust_env=False, headers={"Authorization": "Bearer " + connection.token}, timeout=15) as http:
                async with streamable_http_client(base + "/gradio_api/mcp/", http_client=http) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.list_tools()
            return "连接成功，已识别工具：" + "、".join(tool.name for tool in result.tools)
        except Exception:
            return "连接未成功。请确认正在使用新版启动器，然后重试；仍失败可在启动器查看日志。"

    with gr.Accordion("AI 连接（MCP）", open=False, elem_id="ai-connection-settings"):
        gr.Markdown("让支持本机 MCP 的 AI 助手调用视频转换功能。开启后，复制配置到 AI 客户端添加一次连接即可。")
        enabled = gr.Checkbox(value=connection.enabled, label="允许 AI 助手连接")
        status = gr.Textbox(label="连接状态", interactive=False, value="正在读取设置……")
        address = gr.Textbox(label="MCP 地址（Streamable HTTP）", interactive=False, buttons=["copy"])
        gr.Markdown("连接仅在这台电脑上可用。客户端需支持 Streamable HTTP 和自定义 Authorization 请求头。")
        configuration = gr.Code(label="客户端连接配置", language="json", interactive=False, elem_id="ai-client-config")
        gr.Button("复制连接配置", elem_id="copy-ai-config")
        gr.Markdown("“复制连接配置”包含真实密钥，可直接用于连接；API/MCP 文档中的“复制页面”仅复制说明和密钥占位符。")
        gr.Markdown("当前版本在同一服务内共用一把密钥，尚未提供网站用户账号和每人独立密钥。")
        with gr.Row():
            check = gr.Button("测试连接")
            renew = gr.Button("重新生成连接密钥")
        result = gr.Textbox(label="操作结果", interactive=False)
        gr.Markdown("重置密钥后，已有客户端需要更新配置。关闭连接会拒绝后续调用；已经开始的转换会继续完成。")
        gr.Markdown("**使用方法**：打开连接 → 复制配置 → 在 AI 客户端添加 MCP 服务 → 测试连接。\n\n"
                    "处理本地视频时，AI 客户端还需具备文件上传能力，将视频上传后交给转换工具。")

    outputs = [status, address, configuration]
    enabled.change(update, inputs=enabled, outputs=outputs, api_visibility="private", queue=False)
    check.click(test, outputs=result, api_visibility="private", queue=False)
    renew.click(rotate, outputs=[*outputs, result], api_visibility="private", queue=False)
    gr.on(triggers=None, fn=values, outputs=outputs, api_visibility="private", queue=False)
