"""Exercise a packaged Unova MCP executable without desktop input or save export."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import threading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('executable', 'project-root', 'rom', 'save', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    files = [args.rom, args.save, args.project_root / 'builds/current/melonDS.toml',
             Path(os.environ['APPDATA']) / 'UnovaTogether/launcher.json']
    def hashes():
        result = {}
        for path in files:
            with path.open('rb') as stream:
                result[str(path)] = hashlib.file_digest(stream, 'sha256').hexdigest()
        return result
    before = hashes()
    process = subprocess.Popen([str(args.executable.resolve()), '--project-root',
        str(args.project_root.resolve()), 'mcp'], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        env=dict(os.environ, PYTHONUTF8='0', PYTHONIOENCODING='cp1252'))
    replies = queue.Queue()
    def reader():
        try:
            for line in process.stdout:
                replies.put(json.loads(line.decode('utf-8')))
        except Exception as error:
            replies.put(error)
    threading.Thread(target=reader, daemon=True).start()
    serial = 0
    evidence = []
    session = None
    def request(method, params):
        nonlocal serial
        serial += 1
        process.stdin.write((json.dumps(dict(jsonrpc='2.0', id=serial, method=method,
                                              params=params)) + '\n').encode('utf-8'))
        process.stdin.flush()
        response = replies.get(timeout=90)
        if isinstance(response, Exception):
            raise response
        assert response.get('id') == serial and 'error' not in response, response
        return response['result']
    def call(name, arguments):
        result = request('tools/call', dict(name=name, arguments=arguments))
        assert not result.get('isError'), result
        text = next((c['text'] for c in result['content'] if c['type'] == 'text'), '{}')
        data = json.loads(text)
        evidence.append(dict(tool=name, arguments=arguments, result=data))
        for item in result['content']:
            if item['type'] == 'image':
                image = base64.b64decode(item['data'], validate=True)
                assert image.startswith(b'\x89PNG\r\n\x1a\n')
                (args.output / f'{len(evidence):02d}-{name}.png').write_bytes(image)
        return data
    def control(action, **fields):
        return call('control_emulator', dict(action=action, session=session, **fields))
    try:
        request('initialize', dict(protocolVersion='2025-11-25', capabilities={},
            clientInfo=dict(name='packaged-release-verifier', version='1')))
        listing = request('tools/list', {})
        assert len(listing['tools']) == 13
        assert 'Pokémon' in json.dumps(listing, ensure_ascii=False)
        for model in (4715, 4121):
            metadata = call('preview_player_model', dict(rom=str(args.rom.resolve()), modelId=model))
            assert metadata['frameCount'] > 0 and metadata['width'] > 0
        started = call('start_emulator', dict(rom=str(args.rom.resolve()), save=str(args.save.resolve())))
        session = started['session']
        assert started['romShadowed'] and started['saveIsolated']
        assert control('status')['ok']
        control('wait', frames=60)
        control('press', buttons=['A'], frames=8)
        control('touch', x=128, y=96, frames=2)
        control('pause')
        first = control('status')
        second = control('status')
        assert first['advancing'] is False and first['frame'] == second['frame']
        control('save-state', checkpoint='release-check')
        control('resume')
        control('wait', frames=30)
        control('load-state', checkpoint='release-check')
        control('screenshot')
        control('stop')
        assert not Path(session).exists()
        session = None
    finally:
        if session:
            control('stop')
        process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    assert hashes() == before, 'Original inputs/settings changed'
    report = dict(status='PASS', strictUtf8=True, originalHashes=before, checks=evidence,
                  toolCount=13, processExit=process.returncode)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('PASS: frozen UTF-8 discovery, 2 real previews, normal isolated start, all control actions, stop and unchanged originals')


if __name__ == '__main__':
    main()
