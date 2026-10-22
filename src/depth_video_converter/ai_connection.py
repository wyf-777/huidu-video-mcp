"""Per-user MCP connection settings and an immediate access switch."""

import json
import os
import secrets
import threading
from functools import lru_cache
from pathlib import Path

from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from .mcp_files import LocalUploadMiddleware


class AIConnection:
    def __init__(self, path: Path | None = None):
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".config"))
        self.path = path or root / "DepthVideoConverter" / "ai-connection.json"
        self.lock = threading.RLock()
        self.enabled = False
        self.token = secrets.token_urlsafe(32)
        if self.path.exists():
            config = json.loads(self.path.read_text(encoding="utf-8"))
            self.enabled = config.get("enabled") is True
            self.token = config.get("token") or self.token
        else:
            self.save()

    def save(self):
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps({"enabled": self.enabled, "token": self.token}), encoding="utf-8")
            temporary.replace(self.path)

    def set_enabled(self, enabled: bool):
        with self.lock:
            previous = self.enabled
            self.enabled = bool(enabled)
            try:
                self.save()
            except OSError:
                self.enabled = previous
                raise

    def rotate_token(self):
        with self.lock:
            previous = self.token
            self.token = secrets.token_urlsafe(32)
            try:
                self.save()
            except OSError:
                self.token = previous
                raise

    def client_config(self, base_url: str):
        return {"mcpServers": {"depth-video": {
            "url": base_url.rstrip("/") + "/gradio_api/mcp/",
            "headers": {"Authorization": "Bearer " + self.token},
        }}}


@lru_cache(maxsize=1)
def get_connection():
    return AIConnection()


class MCPAccessMiddleware:
    def __init__(self, app, connection: AIConnection):
        self.app = app
        self.connection = connection

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "").rstrip("/")
        if scope["type"] == "http" and path == "/depth-video/health":
            response = JSONResponse({"application": "depth-video", "settings_version": 1,
                                     "mcp_enabled": self.connection.enabled})
            await response(scope, receive, send)
            return
        is_mcp = path == "/gradio_api/mcp" or path.startswith("/gradio_api/mcp/")
        # The built-in docs can read the public schema; tool calls require the switch and key.
        if scope["type"] == "http" and is_mcp and path != "/gradio_api/mcp/schema":
            if not self.connection.enabled:
                response = JSONResponse({"error": "AI 连接已关闭，请在网页设置中开启。"}, status_code=503)
                await response(scope, receive, send)
                return
            headers = dict(scope.get("headers", []))
            supplied = headers.get(b"authorization", b"")
            expected = ("Bearer " + self.connection.token).encode("ascii")
            if not secrets.compare_digest(supplied, expected):
                response = JSONResponse({"error": "连接密钥不正确，请从网页设置中重新复制配置。"}, status_code=401,
                                        headers={"WWW-Authenticate": "Bearer"})
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


def app_options():
    return {"middleware": [Middleware(MCPAccessMiddleware, connection=get_connection()),
                           Middleware(LocalUploadMiddleware)]}
