"""Small Windows launcher for the local Chinese web UI."""

import json
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk

PROJECT = Path(__file__).resolve().parent
PYTHON = PROJECT / '.venv' / 'Scripts' / 'python.exe'
LOG = PROJECT / 'logs' / 'web-launcher.log'


def is_ready(url):
    try:
        with urllib.request.urlopen(url + '/depth-video/health', timeout=1) as response:
            config = json.load(response)
            return config.get('application') == 'depth-video' and config.get('settings_version') == 1
    except (OSError, ValueError):
        return False


class Launcher:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('深度视频转换器 · 启动器')
        self.window.geometry('470x240')
        self.window.resizable(False, False)
        self.process = None
        self.log_file = None
        self.url = None
        self.result = None
        self.closed = threading.Event()
        frame = ttk.Frame(self.window, padding=24)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='深度视频转换器', font=('Microsoft YaHei UI', 17, 'bold')).pack(anchor='w')
        self.status = tk.StringVar(value='正在启动，请稍候……')
        ttk.Label(frame, textvariable=self.status, wraplength=420).pack(anchor='w', pady=16)
        ttk.Label(frame, text='启动后自动打开浏览器；最小化此窗口可继续使用。\n关闭启动器会停止由它启动的服务。').pack(anchor='w')
        row = ttk.Frame(frame)
        row.pack(anchor='w', pady=18)
        self.open_button = ttk.Button(row, text='打开网页', state='disabled', command=self.open_page)
        self.open_button.pack(side='left', padx=(0, 12))
        ttk.Button(row, text='查看日志', command=self.open_log).pack(side='left', padx=(0, 12))
        ttk.Button(row, text='退出', command=self.close).pack(side='left')
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        threading.Thread(target=self.start, daemon=True).start()
        self.window.after(200, self.poll)

    def start(self):
        try:
            if not PYTHON.is_file():
                raise RuntimeError('未找到 Python 环境，请先按 README.md 安装依赖。')
            existing = 'http://127.0.0.1:7860'
            if is_ready(existing):
                self.result = (existing, '检测到已运行的服务，已打开网页。\n退出本启动器不会停止该服务。')
                return
            with socket.socket() as sock:
                try:
                    sock.bind(('127.0.0.1', 7860))
                except OSError as exc:
                    raise RuntimeError('7860 端口被占用，请先关闭旧版转换器或占用该端口的程序，再重新启动。') from exc
                port = 7860
            url = f'http://127.0.0.1:{port}'
            LOG.parent.mkdir(exist_ok=True)
            self.log_file = LOG.open('w', encoding='utf-8')
            code = (
                'import gradio as gr; '
                'from depth_video_converter.ui import build_app, CSS; '
                'from depth_video_converter.ui_localization import LOCALIZE_JS; '
                'from depth_video_converter.ai_connection import app_options; '
                f'build_app().launch(server_name="127.0.0.1", server_port={port}, '
                'inbrowser=False, css=CSS, theme=gr.themes.Monochrome(), '
                'js=LOCALIZE_JS, footer_links=["api", "settings"], mcp_server=True, app_kwargs=app_options())'
            )
            if self.closed.is_set():
                return
            self.process = subprocess.Popen(
                [str(PYTHON), '-X', 'utf8', '-u', '-c', code], cwd=PROJECT,
                stdout=self.log_file, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for _ in range(180):
                if self.closed.is_set():
                    self.process.terminate()
                    return
                if self.process.poll() is not None:
                    raise RuntimeError('启动失败，请点击“查看日志”查看具体原因。')
                if is_ready(url):
                    self.result = (url, f'服务已就绪：{url}')
                    return
                time.sleep(0.5)
            self.process.terminate()
            raise RuntimeError('启动等待超时，请查看日志后重新打开启动器。')
        except Exception as exc:
            self.result = (None, str(exc))

    def poll(self):
        if self.result is not None:
            self.url, message = self.result
            self.result = None
            self.status.set(message)
            if self.url:
                self.open_button.config(state='normal')
                self.open_page()
        if self.url and self.process and self.process.poll() is not None:
            self.url = None
            self.open_button.config(state='disabled')
            self.status.set('服务已停止，请查看日志或重新打开启动器。')
        if not self.closed.is_set():
            self.window.after(300, self.poll)

    def open_page(self):
        if self.url:
            webbrowser.open(self.url)

    def open_log(self):
        if LOG.exists():
            subprocess.Popen(['notepad.exe', str(LOG)])
        else:
            messagebox.showinfo('日志', '尚未生成日志。', parent=self.window)

    def close(self):
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno('停止服务', '退出将停止视频转换服务，正在进行的转换也会中断。是否退出？', parent=self.window):
                return
        self.closed.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)
        self.window.destroy()


if __name__ == '__main__':
    Launcher().window.mainloop()
