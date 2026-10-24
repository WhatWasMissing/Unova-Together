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

    def test_mcp_modern_discovery_calls_and_legacy_version_counteroffer(self):
        metadata = {
            agent.MCP_VERSION_META: agent.MCP_MODERN_VERSION,
            agent.MCP_CLIENT_INFO_META: {'name': 'unit-test-client', 'version': '1'},
            agent.MCP_CLIENT_CAPABILITIES_META: {},
        }
        discovered = agent._mcp_response({'jsonrpc': '2.0', 'id': 'discover',
            'method': 'server/discover', 'params': {'_meta': metadata}})
        result = discovered['result']
        self.assertEqual(result['resultType'], 'complete')
        self.assertIn(agent.MCP_MODERN_VERSION, result['supportedVersions'])
        self.assertEqual(result['capabilities'], {'tools': {}})
        self.assertEqual(result['_meta'][agent.MCP_SERVER_INFO_META]['name'], 'unova-together-agent-tools')

        listing = agent._mcp_response({'jsonrpc': '2.0', 'id': 'list', 'method': 'tools/list',
            'params': {'_meta': metadata}})
        self.assertEqual(listing['result']['resultType'], 'complete')
        self.assertIn('tools', listing['result'])
        self.assertIsInstance(listing['result']['ttlMs'], int)
        self.assertGreaterEqual(listing['result']['ttlMs'], 0)
        self.assertEqual(listing['result']['cacheScope'], 'public')
        self.assertIn(agent.MCP_SERVER_INFO_META, listing['result']['_meta'])

        called = agent._mcp_response({'jsonrpc': '2.0', 'id': 'call', 'method': 'tools/call',
            'params': {'name': 'project_inventory', 'arguments': {}, '_meta': metadata}})
        self.assertEqual(called['result']['resultType'], 'complete')
        self.assertFalse(called['result']['isError'])

        unsupported_meta = {**metadata, agent.MCP_VERSION_META: '2099-01-01'}
        unsupported = agent._mcp_response({'jsonrpc': '2.0', 'id': 'unsupported',
            'method': 'server/discover', 'params': {'_meta': unsupported_meta}})
        self.assertEqual(unsupported['error']['code'], -32022)
        self.assertIn(agent.MCP_MODERN_VERSION, unsupported['error']['data']['supported'])
        missing_caps = {agent.MCP_VERSION_META: agent.MCP_MODERN_VERSION}
        invalid = agent._mcp_response({'jsonrpc': '2.0', 'id': 'invalid',
            'method': 'server/discover', 'params': {'_meta': missing_caps}})
        self.assertEqual(invalid['error']['code'], -32602)
        self.assertEqual(agent._mcp_response({'jsonrpc': '2.0', 'id': 'bad-init',
            'method': 'initialize', 'params': {'_meta': metadata}})['error']['code'], -32601)
        invalid_client_info = agent._mcp_response({'jsonrpc': '2.0', 'id': 'missing-client-name',
            'method': 'initialize', 'params': {'protocolVersion': '2025-11-25', 'capabilities': {},
                'clientInfo': {'version': '1'}}})
        self.assertEqual(invalid_client_info['error']['code'], -32602)

        for version in agent.MCP_LEGACY_VERSIONS:
            response = agent._mcp_response({'jsonrpc': '2.0', 'id': 'init', 'method': 'initialize',
                'params': {'protocolVersion': version, 'capabilities': {},
                           'clientInfo': {'name': 'test', 'version': '1'}}})
            self.assertEqual(response['result']['protocolVersion'], version)
        counteroffer = agent._mcp_response({'jsonrpc': '2.0', 'id': 'init-new', 'method': 'initialize',
            'params': {'protocolVersion': agent.MCP_MODERN_VERSION, 'capabilities': {},
                       'clientInfo': {'name': 'test', 'version': '1'}}})
        self.assertEqual(counteroffer['result']['protocolVersion'], agent.MCP_LEGACY_VERSIONS[0])

    def test_mcp_start_tool_rejects_custom_executable(self):
        schema = next(tool['inputSchema'] for tool in agent.MCP_TOOLS if tool['name'] == 'start_emulator')
        self.assertNotIn('emulator', schema['properties'])
        with self.assertRaisesRegex(ValueError, 'cannot select an emulator executable'):
            agent.call_tool('start_emulator', {'emulator': 'C:/attacker/melonDS.exe'})

    def test_stdio_supports_legacy_and_modern_request_flows(self):
        modern_metadata = {agent.MCP_VERSION_META: agent.MCP_MODERN_VERSION,
            agent.MCP_CLIENT_INFO_META: {'name': 'stdio-test-client', 'version': '1'},
            agent.MCP_CLIENT_CAPABILITIES_META: {}}
        def run_stdio(requests):
            return subprocess.run([sys.executable, str(Path(agent.__file__)), '--project-root', str(self.root), 'mcp'],
                input='\n'.join(json.dumps(request) for request in requests) + '\n',
                capture_output=True, text=True, timeout=15)

        legacy_process = run_stdio([
            {'jsonrpc': '2.0', 'id': 'early', 'method': 'tools/list'},
            {'jsonrpc': '2.0', 'id': 'init', 'method': 'initialize', 'params': {
                'protocolVersion': '2025-11-25', 'capabilities': {},
                'clientInfo': {'name': 'stdio-test-client', 'version': '1'}}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 'legacy-list', 'method': 'tools/list'},
        ])
        self.assertEqual(legacy_process.returncode, 0, legacy_process.stderr)
        legacy_responses = [json.loads(line) for line in legacy_process.stdout.splitlines()]
        self.assertEqual([response['id'] for response in legacy_responses], ['early', 'init', 'legacy-list'])
        self.assertEqual(legacy_responses[0]['error']['code'], -32600)
        self.assertEqual(legacy_responses[1]['result']['protocolVersion'], '2025-11-25')
        self.assertIn('tools', legacy_responses[2]['result'])

        modern_process = run_stdio([
            {'jsonrpc': '2.0', 'id': 'modern-discover', 'method': 'server/discover',
             'params': {'_meta': modern_metadata}},
            {'jsonrpc': '2.0', 'id': 'modern-list', 'method': 'tools/list',
             'params': {'_meta': modern_metadata}},
        ])
        self.assertEqual(modern_process.returncode, 0, modern_process.stderr)
        modern_responses = [json.loads(line) for line in modern_process.stdout.splitlines()]
        self.assertEqual([response['id'] for response in modern_responses], ['modern-discover', 'modern-list'])
        self.assertEqual(modern_responses[0]['result']['resultType'], 'complete')
        self.assertEqual(modern_responses[1]['result']['resultType'], 'complete')
        self.assertIsInstance(modern_responses[1]['result']['ttlMs'], int)
        self.assertGreaterEqual(modern_responses[1]['result']['ttlMs'], 0)
        self.assertEqual(modern_responses[1]['result']['cacheScope'], 'public')

    def test_stdio_reports_oversized_message_and_continues(self):
        metadata = {agent.MCP_VERSION_META: agent.MCP_MODERN_VERSION,
            agent.MCP_CLIENT_CAPABILITIES_META: {}}
        oversized = 'x' * (agent.MAX_MCP_BODY + 1) + '\n'
        request = json.dumps({'jsonrpc': '2.0', 'id': 'discover', 'method': 'server/discover',
            'params': {'_meta': metadata}}) + '\n'
        process = subprocess.run([sys.executable, str(Path(agent.__file__)), '--project-root', str(self.root), 'mcp'],
            input=oversized + request, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        responses = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(responses[0]['error']['code'], -32600)
        self.assertIsNone(responses[0]['id'])
        self.assertEqual(responses[1]['id'], 'discover')
        self.assertEqual(responses[1]['result']['resultType'], 'complete')

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
            self.assertEqual(response.status, 200, payload)
            self.assertEqual(payload['id'], 2)
            self.assertTrue(payload['result']['isError'])
            self.assertNotIn('structuredContent', payload['result'])
            connection.close()

            modern_metadata = {agent.MCP_VERSION_META: agent.MCP_MODERN_VERSION,
                agent.MCP_CLIENT_INFO_META: {'name': 'http-test-client', 'version': '1'},
                agent.MCP_CLIENT_CAPABILITIES_META: {}}
            modern_body = json.dumps({'jsonrpc': '2.0', 'id': 'modern-list', 'method': 'tools/list',
                                      'params': {'_meta': modern_metadata}})
            modern_headers = {'Authorization': 'Bearer ' + 'a' * 64, 'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream', 'MCP-Protocol-Version': agent.MCP_MODERN_VERSION,
                'Mcp-Method': 'tools/list'}
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request('POST', '/mcp', modern_body, modern_headers)
            response = connection.getresponse(); payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(payload['result']['resultType'], 'complete')
            self.assertIsInstance(payload['result']['ttlMs'], int)
            self.assertGreaterEqual(payload['result']['ttlMs'], 0)
            self.assertEqual(payload['result']['cacheScope'], 'public')
            self.assertEqual(response.getheader('MCP-Protocol-Version'), agent.MCP_MODERN_VERSION)
            connection.close()

            discover_body = json.dumps({'jsonrpc': '2.0', 'id': 'modern-discover', 'method': 'server/discover',
                'params': {'_meta': modern_metadata}})
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request('POST', '/mcp', discover_body,
                {**modern_headers, 'Mcp-Method': 'server/discover'})
            response = connection.getresponse(); payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertIn(agent.MCP_MODERN_VERSION, payload['result']['supportedVersions'])
            self.assertIn(agent.MCP_SERVER_INFO_META, payload['result']['_meta'])
            connection.close()

            tool_call_body = json.dumps({'jsonrpc': '2.0', 'id': 'modern-call', 'method': 'tools/call',
                'params': {'name': 'project_inventory', 'arguments': {}, '_meta': modern_metadata}})
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request('POST', '/mcp', tool_call_body,
                {**modern_headers, 'Mcp-Method': 'tools/call', 'Mcp-Name': 'project_inventory'})
            response = connection.getresponse(); payload = json.loads(response.read())
            self.assertEqual(response.status, 200, payload)
            self.assertEqual(payload['result']['resultType'], 'complete')
            self.assertFalse(payload['result']['isError'])
            connection.close()

            bad_metadata = {**modern_metadata, agent.MCP_VERSION_META: '2099-01-01'}
            missing_version = {key: value for key, value in modern_metadata.items()
                               if key != agent.MCP_VERSION_META}
            cases = (
                (modern_body, {**modern_headers, 'MCP-Protocol-Version': '2025-11-25', 'Mcp-Method': 'tools/list'}, -32020),
                (modern_body, {**modern_headers, 'Mcp-Method': 'tools/call'}, -32020),
                (json.dumps({'jsonrpc': '2.0', 'id': 'bad-version', 'method': 'tools/list',
                    'params': {'_meta': bad_metadata}}),
                    {**modern_headers, 'MCP-Protocol-Version': '2099-01-01'}, -32022),
                (json.dumps({'jsonrpc': '2.0', 'id': 'bad-caps', 'method': 'tools/list',
                    'params': {'_meta': {agent.MCP_VERSION_META: agent.MCP_MODERN_VERSION}}}),
                    modern_headers, -32602),
                (json.dumps({'jsonrpc': '2.0', 'id': 'missing-version', 'method': 'tools/list',
                    'params': {'_meta': missing_version}}), modern_headers, -32602),
            )
            for bad_body, bad_headers, expected_code in cases:
                connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
                connection.request('POST', '/mcp', bad_body, bad_headers)
                response = connection.getresponse(); payload = json.loads(response.read())
                self.assertEqual(response.status, 400)
                self.assertEqual(payload['error']['code'], expected_code)
                connection.close()

            legacy_metadata = {agent.MCP_VERSION_META: '2025-11-25',
                agent.MCP_CLIENT_CAPABILITIES_META: {}}
            legacy_shaped_body = json.dumps({'jsonrpc': '2.0', 'id': 'legacy-meta', 'method': 'tools/list',
                'params': {'_meta': legacy_metadata}})
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request('POST', '/mcp', legacy_shaped_body, {
                **modern_headers, 'MCP-Protocol-Version': '2025-11-25'})
            response = connection.getresponse(); payload = json.loads(response.read())
            self.assertEqual(response.status, 400)
            self.assertEqual(payload['error']['code'], -32602)
            connection.close()

            unknown_header_body = json.dumps({'jsonrpc': '2.0', 'id': 'unknown-header', 'method': 'tools/list'})
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request('POST', '/mcp', unknown_header_body, {
                'Authorization': 'Bearer ' + 'a' * 64, 'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream', 'MCP-Protocol-Version': '2099-01-01'})
            response = connection.getresponse(); payload = json.loads(response.read())
            self.assertEqual(response.status, 400)
            self.assertEqual(payload['error']['code'], -32022)
            self.assertIn(agent.MCP_MODERN_VERSION, payload['error']['data']['supported'])
            connection.close()

            missing_name = {**modern_headers, 'Mcp-Method': 'tools/call'}
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request('POST', '/mcp', tool_call_body, missing_name)
            response = connection.getresponse(); payload = json.loads(response.read())
            self.assertEqual(response.status, 400)
            self.assertEqual(payload['error']['code'], -32020)
            connection.close()

            missing_tool_name_body = json.dumps({'jsonrpc': '2.0', 'id': 'missing-name', 'method': 'tools/call',
                'params': {'arguments': {}, '_meta': modern_metadata}})
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request('POST', '/mcp', missing_tool_name_body, {
                **modern_headers, 'Mcp-Method': 'tools/call'})
            response = connection.getresponse(); payload = json.loads(response.read())
            self.assertEqual(response.status, 400)
            self.assertEqual(payload['error']['code'], -32020)
            connection.close()

            malformed_cases = ((b'{', -32700), (b'[]', -32600),
                (json.dumps({'jsonrpc': '2.0', 'id': 'missing-method'}).encode(), -32600),
                (json.dumps({'jsonrpc': '2.0', 'id': 'unknown', 'method': 'unknown/method'}).encode(), -32601))
            for malformed_body, expected_code in malformed_cases:
                connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
                connection.request('POST', '/mcp', malformed_body, {
                    'Authorization': 'Bearer ' + 'a' * 64, 'Content-Type': 'application/json',
                    'Accept': 'application/json, text/event-stream', 'MCP-Protocol-Version': '2025-03-26'})
                response = connection.getresponse(); payload = json.loads(response.read())
                self.assertEqual(payload['error']['code'], expected_code)
                self.assertEqual(response.status, 404 if expected_code == -32601 else 400)
                connection.close()

            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request('POST', '/mcp', modern_body, {**modern_headers,
                'Accept': 'application/json;q=0, text/event-stream;q=0'})
            response = connection.getresponse(); response.read()
            self.assertEqual(response.status, 406)
            connection.close()

            counteroffer = json.dumps({'jsonrpc': '2.0', 'id': 'legacy-new', 'method': 'initialize',
                'params': {'protocolVersion': agent.MCP_MODERN_VERSION, 'capabilities': {},
                           'clientInfo': {'name': 'legacy-test', 'version': '1'}}})
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            connection.request('POST', '/mcp', counteroffer, legacy_headers if 'legacy_headers' in locals() else {
                'Authorization': 'Bearer ' + 'a' * 64, 'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream'})
            response = connection.getresponse(); payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(payload['result']['protocolVersion'], agent.MCP_LEGACY_VERSIONS[0])
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
