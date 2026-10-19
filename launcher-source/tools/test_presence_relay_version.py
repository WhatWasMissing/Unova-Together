"""Exercise the version and capability fields sent by the production relay."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest

from presence_server import PresenceRelay


class RelayBuildHandshakeTests(unittest.IsolatedAsyncioTestCase):
    async def test_welcome_advertises_relay_build_and_field_zone_support(self):
        with tempfile.TemporaryDirectory(prefix='unova-relay-handshake-') as directory:
            root=Path(directory)
            relay=PresenceRelay(root/'items.json',root/'pokemon.json',build_version='2.0.20')
            server=await asyncio.start_server(relay.client,'127.0.0.1',0,limit=4096)
            try:
                reader,writer=await asyncio.open_connection('127.0.0.1',server.sockets[0].getsockname()[1])
                writer.write(b'{"type":"join","version":1,"name":"launcher-check","room":"handshake-check"}\n')
                await writer.drain()
                welcome=json.loads(await asyncio.wait_for(reader.readline(),1))
                self.assertEqual(welcome['type'],'welcome')
                self.assertEqual(welcome['version'],1)
                self.assertEqual(welcome['buildVersion'],'2.0.20')
                self.assertIs(welcome['fieldZonePresence'],True)
                writer.close();await writer.wait_closed()
            finally:
                server.close();await server.wait_closed()


if __name__=='__main__':unittest.main()
