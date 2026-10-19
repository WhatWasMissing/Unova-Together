"""Two-player encrypted UDP relay with authenticated TLS control; no VPN required."""
import argparse
import asyncio
import json
import os
import secrets
import ssl
import time
from pathlib import Path
from online_wireless_relay import access_key, proof, send, receive
from online_udp_protocol import Cipher, HEADER, MAGIC
import hmac
import re

class Endpoint:
    def __init__(self, writer, room, role):
        self.writer, self.room, self.role = writer, room, role
        self.session = secrets.token_bytes(16)
        self.up_key, self.down_key = secrets.token_bytes(32), secrets.token_bytes(32)
        self.rx, self.tx = Cipher(self.session, self.up_key), Cipher(self.session, self.down_key)
        self.address = None
        self.tokens, self.updated = 2000.0, time.monotonic()
        self.last_udp = self.updated

class Relay(asyncio.DatagramProtocol):
    def __init__(self, key):
        self.key, self.rooms, self.sessions = key, {}, {}
        self.connections = 0
        self.transport = None

    def connection_made(self, transport): self.transport = transport

    def datagram_received(self, packet, address):
        if len(packet) < HEADER.size: return
        magic, session, _ = HEADER.unpack_from(packet)
        endpoint = self.sessions.get(session)
        if magic != MAGIC or endpoint is None: return
        now = time.monotonic()
        endpoint.tokens = min(2000.0, endpoint.tokens + (now-endpoint.updated)*2000)
        endpoint.updated = now
        if endpoint.tokens < 1: return
        endpoint.tokens -= 1
        payload = endpoint.rx.decode(packet)
        if payload is None: return
        endpoint.address, endpoint.last_udp = address, now
        if not payload:
            self.transport.sendto(endpoint.tx.encode(b''), address)
            return
        peer = self.rooms.get(endpoint.room, {}).get('guest' if endpoint.role == 'host' else 'host')
        if peer and peer.address and now-peer.last_udp < 15:
            self.transport.sendto(peer.tx.encode(payload), peer.address)

    async def connection(self, reader, writer):
        self.connections += 1
        endpoint = None
        try:
            if self.connections > 32: return
            nonce = secrets.token_bytes(32)
            await send(writer, 0, nonce)
            kind, raw = await asyncio.wait_for(receive(reader), 10)
            if kind != 0 or len(raw) > 512: return
            hello = json.loads(raw)
            if not isinstance(hello, dict): return
            room, role, auth = hello.get('room'), hello.get('role'), hello.get('auth')
            if not isinstance(room, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,32}', room): return
            if role not in ('host', 'guest') or not isinstance(auth, str): return
            if not hmac.compare_digest(auth, proof(self.key, nonce, room, role)): return
            if room not in self.rooms and len(self.rooms) >= 16: return
            pair = self.rooms.setdefault(room, {})
            if role in pair: return
            endpoint = Endpoint(writer, room, role)
            pair[role] = endpoint
            self.sessions[endpoint.session] = endpoint
            await send(writer, 0, json.dumps(dict(protocol='PPU1', session=endpoint.session.hex(),
                up=endpoint.up_key.hex(), down=endpoint.down_key.hex(),
                udp_port=self.transport.get_extra_info('sockname')[1])).encode())
            if len(pair) == 2:
                for peer in pair.values(): await send(peer.writer, 0, b'paired')
            while True:
                kind, data = await receive(reader)
                if kind != 2 or data: raise ValueError('Invalid control frame')
                await send(writer, 2)
        except (OSError, ValueError, asyncio.TimeoutError, asyncio.IncompleteReadError): pass
        finally:
            if endpoint:
                self.sessions.pop(endpoint.session, None)
                pair = self.rooms.get(endpoint.room, {})
                pair.pop(endpoint.role, None)
                for peer in list(pair.values()):
                    try: await send(peer.writer, 0, b'partner-left')
                    except (OSError, asyncio.TimeoutError): pass
                    peer.writer.close()
                if not pair: self.rooms.pop(endpoint.room, None)
            writer.close()
            try: await writer.wait_closed()
            except OSError: pass
            self.connections -= 1

async def serve(args):
    key = access_key(Path(args.access_key_file).read_text() if args.access_key_file else os.environ.get('POKEPLAY_ONLINE_KEY', ''))
    tls = None
    if args.loopback_test:
        if args.listen != '127.0.0.1': raise ValueError('Plaintext tests are loopback only')
    else:
        if not args.cert or not args.private_key: raise ValueError('TLS certificate and key required')
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        tls.load_cert_chain(args.cert, args.private_key)
    relay = Relay(key)
    transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(lambda: relay, local_addr=(args.listen, args.udp_port))
    try:
        server = await asyncio.start_server(relay.connection, args.listen, args.port, ssl=tls, limit=16384)
        print(f'UDP relay: TCP {args.port} control / UDP {args.udp_port} native traffic', flush=True)
        async with server: await server.serve_forever()
    finally: transport.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--listen', default='0.0.0.0')
    p.add_argument('--port', type=int, default=8766)
    p.add_argument('--udp-port', type=int, default=8767)
    p.add_argument('--cert'); p.add_argument('--private-key'); p.add_argument('--access-key-file')
    p.add_argument('--loopback-test', action='store_true')
    a = p.parse_args()
    if not all(1 <= v <= 65535 for v in (a.port, a.udp_port)): p.error('Invalid port')
    try: asyncio.run(serve(a))
    except KeyboardInterrupt: pass

if __name__ == '__main__': main()
