"""Bound request memory and reject cross-origin browser writes.
This is not authentication. Use a trusted LAN or an authenticated reverse proxy.
"""
from urllib.parse import urlsplit


class RequestLimitMiddleware:
    def __init__(self, app, max_bytes: int = 2 * 1024 * 1024):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope['type'] not in {'http', 'websocket'}:
            return await self.app(scope, receive, send)
        headers = {k.lower(): v.decode('latin-1') for k, v in scope.get('headers', [])}
        origin = headers.get(b'origin')
        host = headers.get(b'host', '')
        write = scope['type'] == 'websocket' or scope.get('method') not in {'GET', 'HEAD', 'OPTIONS'}
        if origin and write and urlsplit(origin).netloc != host:
            if scope['type'] == 'websocket':
                return await send({'type': 'websocket.close', 'code': 1008})
            return await self._reject(send, 403, b'Cross-origin write rejected')
        if scope['type'] == 'websocket' or not write:
            return await self.app(scope, receive, send)
        length = headers.get(b'content-length')
        if length is not None:
            try:
                declared = int(length)
            except ValueError:
                return await self._reject(send, 400, b'Invalid content length')
            if declared < 0 or declared > self.max_bytes:
                return await self._reject(send, 413, b'Request is too large')
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            size += len(chunk)
            if size > self.max_bytes:
                return await self._reject(send, 413, b'Request is too large')
            chunks.append(chunk)
            if not message.get('more_body', False):
                break
        replayed = False
        async def replay():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {'type': 'http.request', 'body': b''.join(chunks), 'more_body': False}
            return await receive()
        return await self.app(scope, replay, send)

    @staticmethod
    async def _reject(send, status, body):
        await send({'type': 'http.response.start', 'status': status,
                    'headers': [(b'content-type', b'text/plain; charset=utf-8'), (b'cache-control', b'no-store')]})
        await send({'type': 'http.response.body', 'body': body})
