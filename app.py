import asyncio
from asyncio import subprocess
import json
import logging
import mimetypes
import os
import sys
from aiohttp import HttpErrorException, Response, EofStream
from aiohttp.server import ServerHttpProtocol
from aiohttp import websocket


BASE_DIR = os.path.dirname(__file__)


def _build_static_files(directory):
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isdir(path):
            yield from _build_static_files(path)
        else:
            with open(path, 'rb') as fobj:
                content = fobj.read()
                length = len(content)
                content_type = mimetypes.guess_type(path)[0]
                if content_type:
                    content_type += '; charset=utf-8'
                else:
                    content_type = 'application/octet-stream'
            yield path, (length, content, content_type)


class HttpServer(ServerHttpProtocol):
    def __init__(self, app, *args, **kwargs):
        self.app = app
        self.django = None
        super().__init__(*args, **kwargs)

    @asyncio.coroutine
    def start(self):
        self.django = yield from self.start_child_process()
        yield from super().start()

    @asyncio.coroutine
    def start_child_process(self):
        return asyncio.create_subprocess_exec(
            'python', 'manage.py', 'showmenu', '--traceback',
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=sys.stderr,
        )

    def send_command(self, command, *args):
        payload = json.dumps(args)
        payload_length = len(payload)
        header = '{}:{}\n'.format(command, payload_length).encode('utf-8')
        self.django.stdin.write(header)
        self.django.stdin.write(payload.encode('utf-8'))

    @asyncio.coroutine
    def read_result(self):
        logging.info('Reading Result')
        length = ''
        guard = 0
        # no clue why this fails sometimes, but this workaround seems to work
        while not length:
            if self.django.returncode is not None:
                logging.info('Child process died, restarting...')
                self.django = yield from self.start_child_process()
            else:
                length_bytes = yield from self.django.stdout.readline()
                length = length_bytes.decode('utf-8').strip()
                logging.info('Length: {!r}'.format(length))
            guard += 1
            if guard > 10:
                raise Exception("Something bad happened")
        payload_length = int(length)
        payload = yield from self.django.stdout.read(payload_length)
        return payload

    @asyncio.coroutine
    def handle_request(self, message, payload):
        value = message.headers.get('UPGRADE', None)
        if value is not None and 'websocket' in value.lower():
            yield from self._handle_websocket(message, payload)
        else:
            yield from self._handle_http(message, payload)

    @asyncio.coroutine
    def _handle_http(self, message, payload):
        logging.info("{} {}".format(message.method, message.path))
        path = message.path

        if path in self.app.static_files:
            return self._serve_static(path)

        elif path == '/':
            return self._index()
        else:
            raise HttpErrorException(404)

    @asyncio.coroutine
    def _handle_websocket(self, message, payload):
        # websocket handshake
        logging.info("WS Connect")
        status, headers, parser, writer = websocket.do_handshake(
            message.method, message.headers, self.transport)

        resp = Response(self.transport, status)
        resp.add_headers(*headers)
        resp.send_headers()

        dataqueue = self.reader.set_parser(parser)

        while True:
            try:
                msg = yield from dataqueue.read()
            except EofStream:
                # client droped connection
                break
            if msg.tp == websocket.MSG_PING:
                writer.pong()
            elif msg.tp == websocket.MSG_CLOSE:
                break
            elif msg.tp == websocket.MSG_TEXT:
                command, args = json.loads(msg.data)
                logging.info("Got Command: {} ({})".format(command, args))
                self.send_command(command, *args)
                result = yield from self.read_result()
                writer.send(result)

        logging.info("WS Disconnect")
        self.send_command('stop')

    def _serve_static(self, path):
        self._send(*self.app.static_files[path])

    def _index(self):
        self._send(self.app.index_page_length, self.app.index_page_html)

    def _send(self, length, content, content_type='text/html'):
        response = Response(self.writer, 200)
        response.add_header('Content-type', content_type)
        response.add_header('Content-length', str(length))
        response.send_headers()
        response.write(content)
        response.write_eof()
        if response.keep_alive():
            self.keep_alive(True)


class App(object):
    def __init__(self, static_dir):
        self.event_loop = asyncio.get_event_loop()

        with open(os.path.join(BASE_DIR, 'home.html'), 'rb') as fobj:
            self.index_page_html = fobj.read()
            self.index_page_length = len(self.index_page_html)

        self.static_files = {}
        for path, data in _build_static_files(static_dir):
            rel_path = os.path.relpath(path, static_dir)
            self.static_files['/static/{}'.format(rel_path)] = data

    def run(self, host, port):
        self.event_loop.run_until_complete(
            self.event_loop.create_server(
                lambda: HttpServer(app=self, loop=self.event_loop),
                host,
                port
            )
        )
        logging.info('Running on {}:{}'.format(host, port))
        try:
            self.event_loop.run_forever()
        except KeyboardInterrupt:
            self.event_loop.stop()

    def stop(self):
        self.event_loop.stop()


def main():
    logging.basicConfig(level=logging.INFO)
    app = App(os.path.join(BASE_DIR, 'static'))
    app.run(
        os.environ.get('BIND_HOST', '0.0.0.0'),
        int(os.environ.get('PORT', 8000))
    )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from raven.base import Client
    client = Client()
    main()
