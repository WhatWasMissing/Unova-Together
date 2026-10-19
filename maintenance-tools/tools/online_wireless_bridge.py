"""Connect native two-player LAN through the online TLS relay.

Host: start a two-player native LAN host, then run this bridge as host.
Guest: run as guest, then join native LAN at 127.0.0.1:17064.
Keep this helper running. Presence still uses its separate shared relay.
"""
import argparse
import asyncio
import json
import os
import re
import socket
import ssl
from online_wireless_relay import access_key, proof, receive, send, MAX_PACKET

class LocalUDP(asyncio.DatagramProtocol):
    def __init__(self, role, target):
        self.role, self.target = role, target
        self.queue = asyncio.Queue(maxsize=128)
        self.transport = None
        self.failure = None
    def connection_made(self, transport): self.transport = transport
    def datagram_received(self, data, address):
        if address[0] != '127.0.0.1' or len(data) > MAX_PACKET: return
        if self.role == 'guest':
            if self.target is None: self.target = address
            elif address != self.target: return  # exactly one emulator endpoint
        elif address != self.target: return
        try: self.queue.put_nowait(data)
        except asyncio.QueueFull:
            self.failure = RuntimeError('Online link overloaded; reconnect instead of dropping native packets')
            self.transport.close()
    def error_received(self, error): self.failure = error

async def bridge(args, status=print):
    tls = None
    if args.loopback_test:
        if args.server != '127.0.0.1': raise ValueError('Plaintext test mode only allows 127.0.0.1')
    else:
        tls = ssl.create_default_context(cafile=args.ca)
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
    reader, writer = await asyncio.wait_for(asyncio.open_connection(args.server, args.port, ssl=tls), 10)
    transport = None
    try:
        kind, nonce = await receive(reader)
        if kind != 0 or len(nonce) != 32: raise ValueError('Wrong online relay protocol')
        key = access_key(args.access_key or os.environ.get('POKEPLAY_ONLINE_KEY', ''))
        await send(writer, 0, json.dumps(dict(room=args.room, role=args.role, auth=proof(key, nonce, args.room, args.role))).encode())
        kind, reply = await receive(reader)
        if kind != 0 or reply != b'waiting': raise ValueError('Relay rejected key, room or role')
        local = LocalUDP(args.role, ('127.0.0.1', args.host_port) if args.role == 'host' else None)
        transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(
            lambda: local, local_addr=('127.0.0.1', 0 if args.role == 'host' else args.local_port), family=socket.AF_INET)
        status('Waiting for partner. ' + ('Host native LAN for 2 players.' if args.role == 'host' else f'Join native LAN at 127.0.0.1:{args.local_port}.'))
        async def outbound():
            while True:
                try: data = await asyncio.wait_for(local.queue.get(), 1)
                except asyncio.TimeoutError:
                    if local.failure: raise local.failure
                    continue
                await send(writer, 1, data)
        async def inbound():
            while True:
                kind, data = await receive(reader)
                if kind == 1 and data:
                    if local.target: transport.sendto(data, local.target)
                elif kind == 0:
                    if data == b'paired': status('Partner connected. Native wireless bridge is active.')
                    elif data == b'partner-left': raise ConnectionError('Partner left; close native LAN and reconnect both bridges')
                    else: raise ValueError('Unexpected relay status')
                elif kind != 2 or data: raise ValueError('Unexpected relay frame')
        async def heartbeat():
            while True:
                await asyncio.sleep(15); await send(writer, 2)
        jobs = [asyncio.create_task(fn()) for fn in (outbound, inbound, heartbeat)]
        try:
            done, _ = await asyncio.wait(jobs, return_when=asyncio.FIRST_COMPLETED)
            for job in done: job.result()
        finally:
            for job in jobs: job.cancel()
            await asyncio.gather(*jobs, return_exceptions=True)
    finally:
        if transport: transport.close()
        writer.close()
        try: await writer.wait_closed()
        except OSError: pass

def wizard(args):
    import tkinter as tk
    from tkinter import ttk
    import threading
    import queue
    root = tk.Tk(); root.title('PokePlay Online Co-op'); root.resizable(False, False)
    fields = {}
    for label, name, default in [('Relay server', 'server', ''), ('Port', 'port', '8766'), ('Room', 'room', 'pokeplay'), ('Access key', 'access_key', '')]:
        row = len(fields); ttk.Label(root, text=label).grid(row=row, column=0, padx=12, pady=6)
        value = tk.StringVar(value=default); fields[name] = value
        ttk.Entry(root, textvariable=value, width=38, show='*' if name == 'access_key' else '').grid(row=row, column=1, padx=12, pady=6)
    role = tk.StringVar(value='guest')
    ttk.Combobox(root, textvariable=role, values=['host', 'guest'], state='readonly').grid(row=4, column=1)
    label = tk.StringVar(value='Host: native LAN for 2. Guest: join 127.0.0.1:17064.\nBoth use the same relay, room and key.')
    ttk.Label(root, textvariable=label, wraplength=400).grid(row=5, columnspan=2, padx=12, pady=12)
    events = queue.Queue(); running = False; loop = None; task = None
    def connect():
        nonlocal running
        if running: return
        try:
            args.server = fields['server'].get().strip(); args.port = int(fields['port'].get())
            args.room = fields['room'].get().strip(); args.role = role.get(); args.access_key = fields['access_key'].get().strip()
            validate(args); access_key(args.access_key)
        except ValueError as error: label.set(str(error)); return
        running = True; button.config(state='disabled'); label.set('Connecting…')
        def worker():
            nonlocal loop, task
            loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
            task = loop.create_task(bridge(args, events.put))
            try: loop.run_until_complete(task)
            except asyncio.CancelledError: pass
            except Exception as error: events.put('Disconnected: ' + str(error))
            finally: loop.close(); events.put(None)
        threading.Thread(target=worker, daemon=True).start()
    def stop():
        if loop and task and not loop.is_closed(): loop.call_soon_threadsafe(task.cancel)
    def poll():
        nonlocal running
        while not events.empty():
            message = events.get()
            if message is None: running = False; button.config(state='normal')
            else: label.set(message)
        root.after(100, poll)
    button = ttk.Button(root, text='Connect', command=connect); button.grid(row=6, column=0, pady=12)
    ttk.Button(root, text='Stop', command=stop).grid(row=6, column=1, pady=12)
    root.protocol('WM_DELETE_WINDOW', lambda: (stop(), root.destroy())); poll(); root.mainloop()

def validate(args):
    if not args.server or not re.fullmatch(r'[a-zA-Z0-9_-]{1,32}', args.room): raise ValueError('Enter a server and room (letters, numbers, _ or -)')
    if any(not 1 <= port <= 65535 for port in (args.port, args.local_port, args.host_port)): raise ValueError('Invalid port')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--server'); p.add_argument('--port', type=int, default=8766)
    p.add_argument('--room', default='pokeplay'); p.add_argument('--role', choices=('host', 'guest'), default='guest')
    p.add_argument('--local-port', type=int, default=17064); p.add_argument('--host-port', type=int, default=7064)
    p.add_argument('--ca'); p.add_argument('--loopback-test', action='store_true'); p.add_argument('--wizard', action='store_true')
    args = p.parse_args(); args.access_key = None
    if args.wizard: wizard(args); return
    validate(args)
    try: asyncio.run(bridge(args))
    except KeyboardInterrupt: pass
    except (OSError, ValueError, asyncio.TimeoutError) as error:
        raise SystemExit('Online connection failed: ' + str(error))

if __name__ == '__main__': main()
