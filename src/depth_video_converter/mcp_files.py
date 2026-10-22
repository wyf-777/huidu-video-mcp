"""Resolve this app's uploaded file URLs without fetching its loopback address."""

import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from gradio.utils import get_upload_folder
from starlette.responses import JSONResponse


def resolve_uploaded_files(value, host: str, upload_root: Path):
    """Only map same-host FileData URLs to existing files inside the upload cache."""
    if isinstance(value, list):
        return [resolve_uploaded_files(item, host, upload_root) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: resolve_uploaded_files(item, host, upload_root) for key, item in value.items()}
    meta = result.get('meta')
    if not isinstance(meta, dict) or meta.get('_type') != 'gradio.FileData':
        return result
    path = result.get('path')
    if not isinstance(path, str):
        return result
    url = urlsplit(path)
    prefix = '/gradio_api/file='
    if url.scheme not in ('http', 'https') or url.netloc.lower() != host.lower() or not url.path.startswith(prefix):
        return result
    local = Path(unquote(url.path[len(prefix):])).resolve()
    if not local.is_relative_to(upload_root.resolve()) or not local.is_file():
        raise ValueError('视频链接不属于已上传的文件，请重新上传视频。')
    result['path'] = str(local)
    return result


class LocalUploadMiddleware:
    """Adapt Gradio queue/API inputs while retaining protection for external URLs."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get('path', '')
        routes = ('/gradio_api/queue/join', '/gradio_api/call/', '/gradio_api/run/', '/gradio_api/api/')
        headers = dict(scope.get('headers', []))
        if (scope['type'] != 'http' or scope.get('method') != 'POST'
                or not path.startswith(routes) or b'application/json' not in headers.get(b'content-type', b'')):
            await self.app(scope, receive, send)
            return

        messages = []
        total = 0
        while True:
            message = await receive()
            messages.append(message)
            total += len(message.get('body', b''))
            if message['type'] != 'http.request' or not message.get('more_body', False) or total > 1024 * 1024:
                break
        if messages[-1]['type'] == 'http.request' and not messages[-1].get('more_body', False) and total <= 1024 * 1024:
            body = b''.join(message.get('body', b'') for message in messages)
            try:
                data = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                pass  # Let Gradio report malformed input using its usual response.
            else:
                try:
                    resolved = resolve_uploaded_files(data, headers.get(b'host', b'').decode('ascii'), Path(get_upload_folder()))
                except ValueError as exc:
                    await JSONResponse({'error': str(exc)}, status_code=400)(scope, receive, send)
                    return
                if resolved != data:
                    body = json.dumps(resolved, ensure_ascii=False).encode('utf-8')
                    messages = [{'type': 'http.request', 'body': body, 'more_body': False}]
                    scope = dict(scope)
                    scope['headers'] = [(key, value) for key, value in scope['headers'] if key != b'content-length']
                    scope['headers'].append((b'content-length', str(len(body)).encode('ascii')))

        async def replay():
            return messages.pop(0) if messages else await receive()

        await self.app(scope, replay, send)
