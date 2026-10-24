"""Focused tests for the project MCP dispatcher and isolated emulator adapter."""
import base64
import http.client
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import unova_agent as agent


class ProjectAgentTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='unova-agent-project-'))
        (self.root / 'docs').mkdir()
        (self.root / 'docs' / 'guide.md').write_text('Native emulator control is opt-in.\n', encoding='utf-8')
        (self.root / 'VERSION.txt').write_text('2.0.32\n', encoding='utf-8')
        agent.configure_paths(self.root)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.root)
        agent.configure_paths()
        agent.ACTIVE_EMULATOR_SESSION = None

    def test_search_and_document_are_project_scoped(self):
        matches = agent.search('opt-in', 'docs')
        self.assertEqual(matches[0]['path'], 'docs/guide.md')
        self.assertIn('Native emulator', agent.read_document('docs/guide.md')['text'])
        with self.assertRaises(ValueError):
            agent.read_document('../outside.txt')

    def test_inventory_and_mcp_discovery(self):
        result = agent.call_tool('project_inventory', {})
        self.assertEqual(result['projectVersion'], '2.0.32')
        response = agent._mcp_response({'jsonrpc': '2.0', 'id': 4, 'method': 'tools/list'})
        names = {tool['name'] for tool in response['result']['tools']}
        self.assertIn('start_emulator', names)
        self.assertIn('preview_player_model', names)
        failed = agent._mcp_response({'jsonrpc': '2.0', 'id': 'bad-rom', 'method': 'tools/call',
            'params': {'name': 'inspect_rom', 'arguments': {'path': str(self.root / 'missing.nds')}}})
        self.assertEqual(failed['id'], 'bad-rom')
        self.assertTrue(failed['result']['isError'])
        self.assertIn('content', failed['result'])
        self.assertNotIn('structuredContent', failed['result'])

    def test_inventory_reads_version_from_installed_runtime_layout(self):
        (self.root / 'VERSION.txt').unlink()
        runtime = self.root / 'builds' / 'current'
        runtime.mkdir(parents=True)
        (runtime / 'VERSION.txt').write_text('Unova Together 2.0.32\n', encoding='utf-8')
        self.assertEqual(agent.inventory()['projectVersion'], 'Unova Together 2.0.32')

    @mock.patch.object(agent.emulator_runner, '_run_command')
    @mock.patch.object(agent.emulator_runner, '_launch')
    def test_start_hides_runner_token_and_control_uses_direct_api(self, launch, command):
        launch.return_value = {
            'ok': True, 'session': 'C:/Temp/unova-agent/session.json', 'pid': 123,
            'version': 'test', 'status': {'paused': False}, 'token': 'secret',
        }
        command.return_value = {'ok': True, 'session': 'C:/Temp/unova-agent/session.json'}
        emulator = self.root / 'melonDS.exe'; emulator.write_bytes(b'emulator')
        rom = self.root / 'game.nds'; rom.write_bytes(b'rom')
        started = agent.start_emulator(str(rom), emulator=str(emulator))
        self.assertNotIn('token', started)
        self.assertTrue(started['romShadowed'])
        pressed = agent.control_emulator('press', buttons=['Up', 'A'], frames=12)
        parsed = command.call_args.args[0]
        self.assertEqual(parsed.operation, 'press')
        self.assertIn('Up', parsed.buttons)
        self.assertEqual(pressed['session'], 'C:/Temp/unova-agent/session.json')

    @mock.patch.object(agent, '_run_runner', return_value={'ok': True})
    def test_mcp_cannot_export_isolated_save(self, run_runner):
        with self.assertRaisesRegex(ValueError, 'local CLI'):
            agent.call_tool('control_emulator', {'action': 'stop', 'session': 'session.json',
                                                   'saveOut': 'C:/outside/export.sav'})
        run_runner.assert_not_called()

    @mock.patch.object(agent, '_run_runner')
    def test_screenshot_adapts_runner_saved_path_to_mcp_image(self, run_runner):
        image = self.root / 'screen.png'
        image.write_bytes(b'\x89PNG\r\n\x1a\nagent-test')
        run_runner.return_value = {'ok': True, 'savedTo': str(image)}
        result = agent.control_emulator('screenshot', session='session.json')
        self.assertEqual(result['path'], str(image.resolve()))
        self.assertEqual(base64.b64decode(result['pngBase64']), image.read_bytes())

    def test_control_input_bounds_fail_before_running_process(self):
        with self.assertRaises(ValueError):
            agent.control_emulator('touch', session='session.json', x=256, y=0)
        with self.assertRaises(ValueError):
            agent.control_emulator('wait', session='session.json', frames=3601)

    def test_loopback_http_requires_bearer_token_and_serves_mcp(self):
        env = dict(os.environ, UNOVA_AGENT_HTTP_TOKEN='a' * 64)
        process = subprocess.Popen([sys.executable, str(Path(agent.__file__)), '--project-root', str(self.root),
                                    'mcp-http', '--port', '0'], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE, text=True, env=env)
        try:
            line = process.stderr.readline()
            match = re.search(r':(\d+)/mcp$', line)
            self.assertIsNotNone(match, line)
            port = int(match.group(1))
            for token, expected in (('wrong-token', 401), ('a' * 64, 200)):
                connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
                body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                                   'params': {'protocolVersion': '2025-03-26', 'capabilities': {},
                                              'clientInfo': {'name': 'test', 'version': '1'}}})
                connection.request('POST', '/mcp', body, {'Authorization': 'Bearer ' + token,
                                   'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'})
                response = connection.getresponse()
                payload = response.read()
                self.assertEqual(response.status, expected)
                if expected == 200:
                    self.assertEqual(json.loads(payload)['result']['protocolVersion'], '2025-03-26')
                    self.assertEqual(response.getheader('MCP-Protocol-Version'), '2025-03-26')
                connection.close()
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            body = json.dumps({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
                               'params': {'name': 'inspect_rom',
                                          'arguments': {'path': str(self.root / 'missing.nds')}}})
            connection.request('POST', '/mcp', body, {'Authorization': 'Bearer ' + 'a' * 64,
                'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
                'MCP-Protocol-Version': '2025-03-26'})
            response = connection.getresponse(); payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(payload['id'], 2)
            self.assertTrue(payload['result']['isError'])
            self.assertNotIn('structuredContent', payload['result'])
            connection.close()
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request('GET', '/mcp', headers={'Authorization': 'Bearer ' + 'a' * 64})
            response = connection.getresponse(); response.read()
            self.assertEqual(response.status, 405)
            connection.close()
            for headers, expected in (({'Content-Type': 'text/plain', 'Accept': 'application/json, text/event-stream'}, 415),
                                      ({'Content-Type': 'application/json', 'Accept': 'application/json'}, 406),
                                      ({'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
                                        'Origin': 'https://untrusted.example'}, 403),
                                      ({'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
                                        'Host': 'untrusted.example'}, 403)):
                connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
                connection.request('POST', '/mcp', '{}', {'Authorization': 'Bearer ' + 'a' * 64, **headers})
                response = connection.getresponse(); response.read()
                self.assertEqual(response.status, expected)
                connection.close()
        finally:
            process.terminate()
            process.wait(timeout=10)
            process.stderr.close()


if __name__ == '__main__':
    unittest.main()
