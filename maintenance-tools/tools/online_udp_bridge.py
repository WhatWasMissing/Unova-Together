"""Experimental encrypted UDP native-LAN bridge. TLS protects room admission."""
import asyncio
import json
import os
import socket
import ssl
import time
import online_wireless_bridge as ui
from online_wireless_relay import access_key, proof, send, receive
from online_udp_protocol import Cipher

class Remote(asyncio.DatagramProtocol):
    def __init__(self, rx, local):
        self.rx, self.local = rx, local
        self.last = time.monotonic()
        self.ready = asyncio.Event()
        self.transport = None
    def connection_made(self, transport): self.transport = transport
    def datagram_received(self, packet, address):
        payload = self.rx.decode(packet)
        if payload is None: return
        self.last = time.monotonic()
        self.ready.set()
        if payload and self.local.target: self.local.transport.sendto(payload, self.local.target)

async def bridge(args, status=print):
    tls = None
    if args.loopback_test:
        if args.server != '127.0.0.1': raise ValueError('Plaintext tests are loopback only')
    else:
        tls = ssl.create_default_context(cafile=args.ca)
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
    reader, writer = await asyncio.wait_for(asyncio.open_connection(args.server, args.port, ssl=tls), 10)
    transports, jobs = [], []
    try:
        kind, nonce = await receive(reader)
        if kind != 0 or len(nonce) != 32: raise ValueError('Wrong relay handshake')
        key = access_key(args.access_key or os.environ.get('POKEPLAY_ONLINE_KEY', ''))
        await send(writer, 0, json.dumps(dict(room=args.room, role=args.role, auth=proof(key, nonce, args.room, args.role))).encode())
        kind, raw = await receive(reader)
        credentials = json.loads(raw)
        if kind != 0 or credentials.get('protocol') != 'PPU1': raise ValueError('UDP relay required')
        session = bytes.fromhex(credentials['session'])
        tx, rx = Cipher(session, bytes.fromhex(credentials['up'])), Cipher(session, bytes.fromhex(credentials['down']))
        local = ui.LocalUDP(args.role, ('127.0.0.1', args.host_port) if args.role == 'host' else None)
        transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(lambda: local,
            local_addr=('127.0.0.1', 0 if args.role == 'host' else args.local_port), family=socket.AF_INET)
        transports.append(transport)
        remote = Remote(rx, local)
        transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(lambda: remote,
            remote_addr=(args.server, int(credentials['udp_port'])), family=socket.AF_INET)
        transports.append(transport)
        transport.sendto(tx.encode(b''))
        await asyncio.wait_for(remote.ready.wait(), 10)
        status(f'UDP reachable. Waiting for partner. Host LAN for 2; guest joins 127.0.0.1:{args.local_port}.')
        async def outbound():
            while True:
                try: payload = await asyncio.wait_for(local.queue.get(), 1)
                except asyncio.TimeoutError:
                    if local.failure: raise local.failure
                    continue
                remote.transport.sendto(tx.encode(payload))
        async def control():
            while True:
                kind, data = await receive(reader)
                if kind == 0 and data == b'paired': status('Partner connected. UDP native wireless active (experimental).')
                elif kind == 0 and data == b'partner-left': raise ConnectionError('Partner left. Return to field; recreate LAN and reconnect both bridges.')
                elif kind != 2 or data: raise ValueError('Unexpected control frame')
        async def heartbeat():
            while True:
                await asyncio.sleep(3)
                if time.monotonic()-remote.last > 15: raise ConnectionError('UDP unreachable. Reconnect or use Tailscale.')
                remote.transport.sendto(tx.encode(b''))
                await send(writer, 2)
        jobs = [asyncio.create_task(fn()) for fn in (outbound, control, heartbeat)]
        done, _ = await asyncio.wait(jobs, return_when=asyncio.FIRST_COMPLETED)
        for job in done: job.result()
    finally:
        for job in jobs: job.cancel()
        await asyncio.gather(*jobs, return_exceptions=True)
        for transport in transports: transport.close()
        writer.close()
        try: await writer.wait_closed()
        except OSError: pass

if __name__ == '__main__':
    ui.bridge = bridge
    ui.main()
