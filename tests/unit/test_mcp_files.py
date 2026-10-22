"""Regression checks for MCP uploads without disabling external URL protection."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from depth_video_converter.mcp_files import LocalUploadMiddleware


class LocalUploadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'uploads'
        self.root.mkdir()
        self.video = self.root / '测试视频.mp4'
        self.video.write_bytes(b'test fixture')

        async def echo(request):
            return JSONResponse(await request.json())

        app = Starlette(routes=[Route('/gradio_api/queue/join', echo, methods=['POST'])])
        app.add_middleware(LocalUploadMiddleware)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        patcher = patch('depth_video_converter.mcp_files.get_upload_folder', return_value=str(self.root))
        patcher.start()
        self.addCleanup(patcher.stop)

    def payload(self, path, host='testserver'):
        return {'data': [{'video': {'path': 'http://' + host + '/gradio_api/file=' + quote(str(path), safe='/:'),
                                   'meta': {'_type': 'gradio.FileData'}}}]}

    def test_uploaded_unicode_video_url_is_resolved(self):
        response = self.client.post('/gradio_api/queue/join', json=self.payload(self.video))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data'][0]['video']['path'], str(self.video.resolve()))

    def test_other_hosts_are_left_to_gradio_url_protection(self):
        body = self.payload(self.video, host='192.168.1.100')
        response = self.client.post('/gradio_api/queue/join', json=body)
        self.assertEqual(response.json(), body)

    def test_files_outside_upload_folder_are_rejected(self):
        outside = self.root.parent / 'private.txt'
        outside.write_bytes(b'not uploaded')
        response = self.client.post('/gradio_api/queue/join', json=self.payload(outside))
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('not uploaded', response.text)

    def test_missing_uploaded_files_are_rejected(self):
        response = self.client.post('/gradio_api/queue/join', json=self.payload(self.root / 'missing.mp4'))
        self.assertEqual(response.status_code, 400)

    def test_large_or_malformed_requests_are_forwarded_unchanged(self):
        for data in [b'{invalid-json', b'"' + b'x' * (1024 * 1024) + b'"']:
            # Use an endpoint that returns the raw body to verify ASGI replay.
            async def echo_bytes(request):
                from starlette.responses import Response
                return Response(await request.body())

            app = Starlette(routes=[Route('/gradio_api/queue/join', echo_bytes, methods=['POST'])])
            app.add_middleware(LocalUploadMiddleware)
            with TestClient(app) as client:
                response = client.post('/gradio_api/queue/join', content=data, headers={'Content-Type': 'application/json'})
            self.assertEqual(response.content, data)


if __name__ == '__main__':
    unittest.main()
