import asyncio
from asyncio import subprocess
import json
from pprint import pprint
import sys


def send_command(writer, command, *args):
    payload = json.dumps(args)
    payload_length = len(payload)
    header = '{}:{}\n'.format(command, payload_length).encode('utf-8')
    writer.write(header)
    writer.write(payload.encode('utf-8'))


@asyncio.coroutine
def read_result(reader):
    length = yield from reader.readline()
    payload = yield from reader.read(int(length.decode('utf-8')))
    return payload


@asyncio.coroutine
def render_tree(tree):
    proc = yield from asyncio.create_subprocess_exec(
        'python', 'manage.py', 'showmenu', '--traceback',
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=sys.stderr,
    )
    send_command(proc.stdin, 'set_tree', tree)
    menu = yield from read_result(proc.stdout)
    send_command(proc.stdin, 'stop')
    proc.wait()
    return json.loads(menu.decode('utf-8'))


def main():
    loop = asyncio.get_event_loop()
    coro = render_tree([
        {'title': 'home', 'items':[
            {'title': 'sub-home', 'items': []}
        ]},
        {'title': 'sibling', 'items': []}
    ])
    result = loop.run_until_complete(coro)
    pprint(result)
    loop.close()

if __name__ == '__main__':
    main()
