"""Bounded two-player TLS tunnel for native ENet wireless datagrams.

Deploy on a reachable server. Players make outbound connections; their native
host/guest roles and every ENet datagram remain unchanged. No ROM/save storage.
"""
import argparse
import asyncio
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import ssl
import struct

MAX_PACKET = 8192
HEADER = struct.Struct('!BH')

async def send(writer, kind, payload=b''):
    if len(payload) > MAX_PACKET: raise ValueError('Oversized tunnel frame')
    writer.write(HEADER.pack(kind, len(payload)) + payload)
    await asyncio.wait_for(writer.drain(), 5)

async def receive(reader):
    kind, size = HEADER.unpack(await asyncio.wait_for(reader.readexactly(3), 45))
    if size > MAX_PACKET: raise ValueError('Oversized tunnel frame')
    return kind, await asyncio.wait_for(reader.readexactly(size), 5)

def proof(key, nonce, room, role):
    return hmac.new(key, nonce + b'\0' + room.encode('ascii') + b'\0' + role.encode('ascii'), hashlib.sha256).hexdigest()

def access_key(value):
    if not re.fullmatch(r'[0-9a-fA-F]{64}', value.strip()):
        raise ValueError('Access key must be 64 hex characters (32 random bytes)')
    return bytes.fromhex(value.strip())

class Relay:
    def __init__(self, key):
        self.key, self.rooms, self.connections = key, {}, 0

    async def connection(self, reader, writer):
        room = role = None
        self.connections += 1
        try:
            if self.connections > 32: return
            nonce = secrets.token_bytes(32)
            await send(writer, 0, nonce)
            kind, raw = await asyncio.wait_for(receive(reader), 10)
            if kind != 0 or len(raw) > 512: return
            hello = json.loads(raw)
            if not isinstance(hello, dict): return
            proposed_room, proposed_role = hello.get('room'), hello.get('role')
            if not isinstance(proposed_room, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,32}', proposed_room) or proposed_role not in ('host', 'guest'):
                return
            room, role = proposed_room, proposed_role
            auth = hello.get('auth', '')
            if not isinstance(auth, str) or not hmac.compare_digest(auth, proof(self.key, nonce, room, role)): return
            if room not in self.rooms and len(self.rooms) >= 16: return
            pair = self.rooms.setdefault(room, {})
            if role in pair: return
            pair[role] = writer
            other = 'guest' if role == 'host' else 'host'
            await send(writer, 0, b'waiting')
            if other in pair:
                await send(pair[other], 0, b'paired')
                await send(writer, 0, b'paired')
            while True:
                kind, payload = await receive(reader)
                if kind == 2 and not payload:
                    await send(writer, 2)
                elif kind == 1 and payload:
                    target = pair.get(other)
                    if target: await send(target, 1, payload)
                else: raise ValueError('Unexpected tunnel frame')
        except (OSError, ValueError, asyncio.IncompleteReadError, asyncio.TimeoutError):
            pass
        finally:
            pair = self.rooms.get(room, {})
            if pair.get(role) is writer:
                pair.pop(role)
                for peer in list(pair.values()):
                    try: await send(peer, 0, b'partner-left')
                    except (OSError, asyncio.TimeoutError): pass
                    peer.close()
                if not pair: self.rooms.pop(room, None)
            writer.close()
            try: await writer.wait_closed()
            except OSError: pass
            self.connections -= 1

async def serve(args):
    key = access_key(Path(args.access_key_file).read_text() if args.access_key_file else os.environ.get('POKEPLAY_ONLINE_KEY', ''))
    tls = None
    if not args.loopback_test:
        if not args.cert or not args.private_key: raise ValueError('Public relay requires --cert and --private-key')
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        tls.load_cert_chain(args.cert, args.private_key)
    elif args.listen != '127.0.0.1': raise ValueError('Plaintext test mode is restricted to 127.0.0.1')
    relay = Relay(key)
    server = await asyncio.start_server(relay.connection, args.listen, args.port, ssl=tls, limit=MAX_PACKET * 2)
    print(f'Native wireless relay listening on {args.listen}:{args.port}', flush=True)
    async with server: await server.serve_forever()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--listen', default='0.0.0.0'); p.add_argument('--port', type=int, default=8766)
    p.add_argument('--cert'); p.add_argument('--private-key'); p.add_argument('--access-key-file')
    p.add_argument('--loopback-test', action='store_true')
    args = p.parse_args()
    if not 1 <= args.port <= 65535: p.error('Invalid port')
    try: asyncio.run(serve(args))
    except KeyboardInterrupt: pass
    except (OSError, ValueError) as error:
        raise SystemExit('Online relay failed: ' + str(error))

if __name__ == '__main__': main()
