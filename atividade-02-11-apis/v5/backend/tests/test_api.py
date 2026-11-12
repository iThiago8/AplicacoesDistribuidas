import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app.app)
        self.key_patch = patch.object(app, "CHAVE_API", "chave-de-teste")
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)

    def upstream(self, handler):
        original = httpx.AsyncClient
        return patch.object(app.httpx, "AsyncClient", side_effect=lambda **kwargs:
                            original(transport=httpx.MockTransport(handler), **kwargs))

    def test_missing_key(self):
        with patch.object(app, "CHAVE_API", None):
            self.assertEqual(self.client.get('/api/canal?handle=@NASA').status_code, 503)

    def test_channel_mapping_and_secret(self):
        def handler(request):
            self.assertEqual(request.url.params['key'], 'chave-de-teste')
            return httpx.Response(200, json={'items': [{
                'snippet': {'title': 'NASA'},
                'contentDetails': {'relatedPlaylists': {'uploads': 'uploads-nasa'}}}]})
        with self.upstream(handler):
            response = self.client.get('/api/canal?handle=@NASA')
        self.assertEqual(response.json(), {'titulo': 'NASA', 'playlist': 'uploads-nasa'})
        self.assertNotIn('chave-de-teste', response.text)

    def test_pagination_and_video_mapping(self):
        def handler(request):
            self.assertEqual(request.url.params['pageToken'], 'pagina-2')
            self.assertEqual(request.url.params['maxResults'], '12')
            return httpx.Response(200, json={'nextPageToken': 'pagina-3', 'items': [
                {'snippet': {'resourceId': {'videoId': 'abc'}, 'title': 'Vídeo',
                             'thumbnails': {'medium': {'url': 'https://example.com/img.jpg'}}}},
                {'snippet': {}}]})
        with self.upstream(handler):
            response = self.client.get('/api/videos?playlist=uploads&page_token=pagina-2')
        data = response.json()
        self.assertEqual(data['nextPageToken'], 'pagina-3')
        self.assertEqual(len(data['videos']), 1)
        self.assertEqual(data['videos'][0]['videoId'], 'abc')
        self.assertNotIn('chave-de-teste', response.text)

    def test_not_found_quota_and_network(self):
        for code, payload, expected in [(200, {'items': []}, 404), (403, {}, 403)]:
            with self.upstream(lambda request: httpx.Response(code, json=payload)):
                self.assertEqual(self.client.get('/api/canal?handle=@NASA').status_code, expected)
        def timeout(request):
            raise httpx.ConnectTimeout('timeout', request=request)
        with self.upstream(timeout):
            self.assertEqual(self.client.get('/api/canal?handle=@NASA').status_code, 503)

    def test_validation_and_cors(self):
        self.assertEqual(self.client.get('/api/videos?playlist=x&max_results=51').status_code, 422)
        response = self.client.get('/', headers={'Origin': 'http://localhost:5500'})
        self.assertEqual(response.headers['access-control-allow-origin'], 'http://localhost:5500')


if __name__ == '__main__':
    unittest.main()
