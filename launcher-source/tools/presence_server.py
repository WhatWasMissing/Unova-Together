"""Optional local/LAN presence relay. Python standard library only; no game files."""
import argparse
import asyncio
import contextlib
import json
import math
import time
import uuid
from pathlib import Path
from item_trading_relay import ItemTrades
from pokemon_trading_relay import PokemonTrades
from coop_social import CoopSocial
from dataclasses import dataclass, field

MAX_LINE = 98304

def integer(value, low, high):
    return type(value) is int and low <= value <= high

def validate_state(message, previous_sequence):
    sequence = message.get('sequence')
    if not integer(sequence, 0, 2**53 - 1) or sequence <= previous_sequence:
        raise ValueError('Invalid state sequence')
    if type(message.get('active')) is not bool:
        raise ValueError('Invalid active flag')
    result = {'sequence': sequence, 'active': message['active']}
    if 'coopProtocol' in message:
        if not integer(message['coopProtocol'],1,65535):raise ValueError('Invalid co-op protocol')
        result['coopProtocol']=message['coopProtocol']
    if 'modVersion' in message:
        value=message['modVersion']
        if type(value) is not str or not 1<=len(value)<=32 or not all(c.isascii() and (c.isalnum() or c in '.-') for c in value):raise ValueError('Invalid mod version')
        result['modVersion']=value
    if 'romFingerprint' in message:
        value=message['romFingerprint']
        if type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('Invalid ROM fingerprint')
        result['romFingerprint']=value
    for key in ('shareBattle',):
        if key in message:
            if type(message[key]) is not bool:
                raise ValueError('Invalid co-op option')
            result[key] = message[key]
    if 'coopStatus' in message:
        if message['coopStatus'] not in ('ready','menu','waiting','preparing','battle','busy'):
            raise ValueError('Invalid co-op status')
        result['coopStatus'] = message['coopStatus']
    if 'inMenu' in message:
        if type(message['inMenu']) is not bool:
            raise ValueError('Invalid menu flag')
        result['inMenu'] = message['inMenu']
    if 'inBattle' in message:
        if type(message['inBattle']) is not bool:
            raise ValueError('Invalid battle flag')
        result['inBattle'] = message['inBattle']
    if 'activity' in message:
        if message['activity'] not in ('ready', 'busy', 'battle'):
            raise ValueError('Invalid player activity')
        result['activity'] = message['activity']
    if 'nativeLANReady' in message:
        if type(message['nativeLANReady']) is not bool:
            raise ValueError('Invalid native LAN readiness')
        result['nativeLANReady'] = message['nativeLANReady']
    if not result['active']:
        return result
    # Field zones are required alongside map IDs for safe in-game warps. The
    # emulator reports -1 or 0xffff when it cannot resolve a live zone; omit
    # those sentinels so clients can reject a teleport to an unknown zone.
    if 'fieldZone' in message:
        value=message['fieldZone']
        if type(value) is not int or value < -1 or value > 65535:
            raise ValueError('Invalid field zone')
        if 0 <= value < 65535:
            result['fieldZone']=value
    for key, limit in [('followerSpecies',649), ('followerForm',31), ('followerGender',2)]:
        if key in message:
            if not integer(message[key],0,limit):
                raise ValueError('Invalid follower metadata')
            result[key]=message[key]
    if 'followerShiny' in message:
        if type(message['followerShiny']) is not bool:raise ValueError('Invalid follower shininess')
        result['followerShiny']=message['followerShiny']
    for key, low, high in [('map', 1, 65535), ('tileX', 0, 65535), ('tileZ', 0, 65535)]:
        if not integer(message.get(key), low, high):
            raise ValueError('Invalid coordinate or map')
        result[key] = message[key]
    for key in ('smoothX', 'smoothZ'):
        value = message.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or not -1 <= value <= 65535:
            raise ValueError('Invalid continuous coordinate')
        result[key] = value
    if abs(result['smoothX'] - result['tileX']) > 1.01 or abs(result['smoothZ'] - result['tileZ']) > 1.01:
        raise ValueError('Tile and continuous position disagree')
    if message.get('facing') not in ('North', 'South', 'West', 'East'):
        raise ValueError('Invalid facing')
    if type(message.get('moving')) is not bool:
        raise ValueError('Invalid movement flag')
    result['facing'] = message['facing']
    result['moving'] = message['moving']
    if 'worldY' in message:
        height = message['worldY']
        if type(height) not in (int, float) or not math.isfinite(height) or not -32768 <= height <= 32768:
            raise ValueError('Invalid world height')
        result['worldY'] = height
    if 'avatar' in message:
        if not integer(message['avatar'], 0, 1):
            raise ValueError('Invalid trainer choice')
        result['avatar'] = message['avatar']
    return result

@dataclass
class Peer:
    writer: asyncio.StreamWriter
    room: str
    name: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    state: dict = field(default_factory=lambda: {'active': False})
    last_active_state: dict = field(default_factory=lambda: {'active': False})
    last_active_updated: float = 0.0
    sequence: int = -1
    updated: float = field(default_factory=time.monotonic)
    rate_start: float = field(default_factory=time.monotonic)
    rate_count: int = 0
    interactions: bool = False
    last_request: float = -10
    item_client: str = ''
    pokemon_trading: bool = False
    overworld_battles: bool = False

class PresenceRelay:
    def __init__(self, item_journal=None, pokemon_journal=None, build_version='unknown'):
        self.peers = {}
        self.connections = 0
        self.build_version = str(build_version)[:32]
        self.sessions = {}
        self.checkpoints = {}
        self.social = CoopSocial(self)
        self.item_trades = ItemTrades(self, item_journal or Path(__file__).resolve().parents[1]/'transfer/item-transfers.json')
        self.pokemon_trades = PokemonTrades(self, pokemon_journal or self.item_trades.path.with_name('pokemon-transfers.json'))

    def checkpoint_action(self, peer, message):
        def reject(reason): self.send(peer, {'type':'checkpoint_error','reason':reason})
        challenge=self.checkpoints.get(peer.room)
        if message.get('action')=='cancel':
            if challenge and peer.id in challenge['participants'] and challenge['status']=='active':
                challenge['status']='cancelled'
            return
        if message.get('action')!='create': reject('Unknown checkpoint action.'); return
        if challenge and challenge['status']=='active': reject('Finish or cancel the current checkpoint first.'); return
        other=self.peers.get(message.get('target')) if isinstance(message.get('target'),str) else None
        now=time.monotonic()
        def available(p): return p and p.state.get('active') and not p.state.get('inBattle') and now-p.updated<2
        if not other or other.id==peer.id or other.room!=peer.room or not available(peer) or not available(other):
            reject('Choose a connected player; both players must be in the overworld.'); return
        if now-peer.last_request<2: reject('Wait two seconds before setting another checkpoint.'); return
        peer.last_request=now
        self.checkpoints[peer.room]={'id':uuid.uuid4().hex,'status':'active','map':peer.state['map'],
            'x':peer.state['smoothX'],'z':peer.state['smoothZ'],'radius':1,
            'participants':[peer.id,other.id],'names':[peer.name,other.name],'arrived':[]}

    def update_checkpoints(self, now):
        for room,challenge in list(self.checkpoints.items()):
            if not any(p.room==room for p in self.peers.values()):
                del self.checkpoints[room]; continue
            if challenge['status']!='active': continue
            participants=[self.peers.get(pid) for pid in challenge['participants']]
            if any(p is None for p in participants):
                challenge['status']='cancelled'; continue
            challenge['arrived']=[p.id for p in participants if p.state.get('active') and not p.state.get('inBattle')
                and now-p.updated<2 and p.state.get('map')==challenge['map']
                and math.hypot(p.state['smoothX']-challenge['x'],p.state['smoothZ']-challenge['z'])<=challenge['radius']]
            if len(challenge['arrived'])==2: challenge['status']='complete'

    def send(self, peer, message):
        if peer.writer.is_closing():
            return
        buffered = peer.writer.transport.get_write_buffer_size()
        # Optional previews must never fill the presence/trading queue.
        if message.get('type') == 'coop' and message.get('action') == 'frame' and buffered > 32768:
            return
        if buffered > 131072:
            peer.writer.close()
            return
        peer.writer.write((json.dumps(message, allow_nan=False) + '\n').encode())

    def nearby(self, a, b, allow_busy=False, allow_inactive=False):
        now = time.monotonic()
        def current_location(peer):
            if peer.state.get('active'):
                return peer.state
            if (not allow_inactive or not peer.last_active_state.get('active') or
                    (not allow_busy and now-peer.last_active_updated >= 2)):
                return None
            return {**peer.last_active_state,
                    'inBattle': peer.state.get('inBattle', False),
                    'activity': peer.state.get('activity', peer.last_active_state.get('activity'))}

        a_state, b_state = current_location(a), current_location(b)
        return (a.room == b.room and a_state is not None and b_state is not None
                and not a.state.get('inBattle') and not b.state.get('inBattle')
                and a.state.get('activity') != 'battle' and b.state.get('activity') != 'battle'
                and (allow_busy or (a_state.get('activity') != 'busy' and b_state.get('activity') != 'busy'))
                and now-a.updated < 2 and now-b.updated < 2
                and a_state.get('map') == b_state.get('map'))

    def notify_session(self, session, status, reason=''):
        for pid in (session['from'], session['to']):
            peer = self.peers.get(pid)
            if peer:
                self.send(peer, {'type':'interaction', **{k:v for k,v in session.items() if k != 'expires'},
                                 'status':status, 'reason':reason})

    def finish(self, sid, status, reason=''):
        trade = self.pokemon_trades.trades.get(sid)
        if trade and trade['status'] in ('committed', 'complete'):
            # A disconnect or Cancel cannot undo a durably committed party swap.
            return
        if trade and trade['status'] in ('selecting', 'confirming', 'preparing'):
            try:
                self.pokemon_trades.cancel(trade, reason or 'Pokemon trade cancelled.')
            except OSError:
                for peer in self.pokemon_trades.peers(trade):
                    if peer:
                        self.pokemon_trades.error(peer, 'Relay cannot save the cancellation. Pokemon remain unchanged.')
            return
        session = self.sessions.pop(sid)
        self.notify_session(session, status, reason)

    def interaction(self, peer, message):
        def reject(reason):
            self.send(peer, {'type':'interaction_error', 'reason':reason})
        if not peer.interactions:
            reject('Update your client to use interactions.'); return
        action = message.get('action')
        if action == 'request':
            now = time.monotonic()
            if now-peer.last_request < 2:
                reject('Wait two seconds before another request.'); return
            peer.last_request = now
            target_id = message.get('target')
            target = self.peers.get(target_id) if isinstance(target_id, str) else None
            kind = message.get('kind')
            if not target or target is peer or not target.interactions or kind not in ('trade','battle'):
                reject('Player unavailable or client does not support interactions.'); return
            if kind == 'battle' and (not peer.overworld_battles or not target.overworld_battles):
                reject('Update both players to use overworld battles.'); return
            if kind == 'trade' and peer.pokemon_trading != target.pokemon_trading:
                reject('Update both players to use overworld Pokemon trades.'); return
            if kind == 'battle' and (message.get('lanReady') is False or
                    peer.state.get('nativeLANReady') is False or target.state.get('nativeLANReady') is False):
                reject('Both players must join the same ready native LAN session before battling.'); return
            if not self.nearby(peer, target):
                reject('Both players must be ready on the same map.'); return
            if any(peer.id in (s['from'],s['to']) or target.id in (s['from'],s['to']) for s in self.sessions.values()):
                reject('One player already has an interaction open.'); return
            if self.pokemon_trades.busy(peer.item_client, target.item_client):
                reject('Finish the pending Pokemon trade first.'); return
            if any(t['status'] in ('offered','preparing','committed') and
                   (peer.item_client in (t['fromClient'],t['toClient']) or target.item_client in (t['fromClient'],t['toClient']))
                   for t in self.item_trades.trades.values()):
                reject('Finish the item transfer first.'); return
            sid = uuid.uuid4().hex
            session = {'id':sid, 'from':peer.id, 'to':target.id, 'fromName':peer.name,
                       'toName':target.name, 'kind':kind, 'status':'pending', 'expires':now+30}
            session['directPokemonTrade'] = kind == 'trade' and peer.pokemon_trading and target.pokemon_trading
            self.sessions[sid] = session
            self.notify_session(session, 'pending')
        elif action in ('accept','decline','cancel','complete'):
            sid = message.get('id')
            session = self.sessions.get(sid) if isinstance(sid,str) else None
            if not session or peer.id not in (session['from'],session['to']):
                reject('Interaction is no longer available.'); return
            if action == 'cancel':
                trade = self.pokemon_trades.trades.get(sid)
                if trade and trade['status'] in ('committed', 'complete'):
                    self.pokemon_trades.notify(trade); return
                self.finish(sid,'cancelled'); return
            if action == 'complete':
                if session['status'] != 'accepted' or session['kind'] != 'battle':
                    reject('Only an accepted battle can complete through this action.'); return
                self.finish(sid,'complete'); return
            if peer.id != session['to'] or session['status'] != 'pending':
                reject('Only the recipient can respond to a pending request.'); return
            if action == 'decline':
                self.finish(sid,'declined'); return
            a,b = self.peers.get(session['from']),self.peers.get(session['to'])
            if time.monotonic() >= session['expires'] or not a or not b or not self.nearby(a,b,allow_inactive=True):
                self.finish(sid,'cancelled','Request expired or players are no longer on the same map.'); return
            if session['kind'] == 'battle' and (a.state.get('nativeLANReady') is False or b.state.get('nativeLANReady') is False):
                self.finish(sid, 'cancelled', 'Native LAN is no longer ready.'); return
            session['status'] = 'accepted'
            session['expires'] = time.monotonic()+300
            trade = None
            if session.get('directPokemonTrade'):
                try:
                    trade = self.pokemon_trades.start(session)
                except (OSError, ValueError):
                    session['status'] = 'pending'
                    session['expires'] = time.monotonic()+30
                    reject('Pokemon trade could not start. Check the relay journal and retry.'); return
            self.notify_session(session,'accepted')
            if trade:
                self.pokemon_trades.notify(trade)
        else:
            reject('Unknown interaction action.')

    async def read(self, reader):
        line = await asyncio.wait_for(reader.readline(), 10)
        if not line:
            return None
        if len(line) > MAX_LINE or not line.endswith(b'\n'):
            raise ValueError('Oversized or unfinished message')
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError('Expected message object')
        return value

    async def client(self, reader, writer):
        peer = None
        self.connections += 1
        try:
            if self.connections > 32:
                raise ValueError('Relay full')
            join = await self.read(reader)
            if not join or join.get('type') != 'join' or join.get('version') != 1:
                raise ValueError('Expected version 1 join')
            room, name = join.get('room'), join.get('name')
            if not isinstance(room, str) or not 1 <= len(room) <= 64 or not room.isprintable():
                raise ValueError('Invalid room')
            if not isinstance(name, str) or not 1 <= len(name) <= 32 or not name.isprintable():
                raise ValueError('Invalid name')
            peer = Peer(writer, room, name)
            peer.interactions = join.get('interactions') is True
            peer.pokemon_trading = join.get('pokemonTrading') is True
            peer.overworld_battles = join.get('overworldBattles') is True
            token=join.get('itemClient', '')
            if isinstance(token,str) and len(token)==32 and all(c in '0123456789abcdef' for c in token):
                if any(p.item_client==token for p in self.peers.values()): raise ValueError('Duplicate item client identity')
                peer.item_client=token
            self.peers[peer.id] = peer
            writer.write((json.dumps({'type': 'welcome', 'version': 1, 'buildVersion': self.build_version, 'id': peer.id, 'interactions': True, 'battlePresence': True, 'checkpoints': True, 'fieldZonePresence': True, 'itemTrading': True, 'itemRecovery': True, 'pokemonTrading': True, 'overworldBattles': True, 'coopSocial': True}) + '\n').encode())
            await writer.drain()
            self.item_trades.resume(peer)
            self.pokemon_trades.resume(peer)
            while message := await self.read(reader):
                now = time.monotonic()
                if now - peer.rate_start >= 1:
                    peer.rate_start, peer.rate_count = now, 0
                peer.rate_count += 1
                if peer.rate_count > 60:
                    raise ValueError('State rate exceeded')
                if message.get('type') == 'coop':
                    self.social.action(peer,message)
                    continue
                if message.get('type') == 'checkpoint':
                    self.checkpoint_action(peer,message)
                    continue
                if message.get('type') == 'item_trade':
                    self.item_trades.action(peer,message)
                    continue
                if message.get('type') == 'pokemon_trade':
                    self.pokemon_trades.action(peer, message)
                    continue
                if message.get('type') == 'interaction':
                    self.interaction(peer, message)
                    continue
                if message.get('type') != 'state':
                    raise ValueError('Expected state or interaction')
                peer.state = validate_state(message, peer.sequence)
                peer.sequence = peer.state['sequence']
                peer.updated = now
                if peer.state.get('active'):
                    peer.last_active_state = peer.state.copy()
                    peer.last_active_updated = now
        except (ValueError, UnicodeError, ConnectionError, asyncio.TimeoutError):
            pass
        finally:
            if peer:
                for sid,s in list(self.sessions.items()):
                    if peer.id in (s['from'],s['to']):
                        self.finish(sid,'cancelled','Player disconnected.')
                self.peers.pop(peer.id, None)
                self.social.tick()
                # Abort uncommitted inventory holds immediately, before an identity
                # can reconnect under a new peer ID. Commit decisions stay durable.
                self.item_trades.tick()
                self.pokemon_trades.tick()
            self.connections -= 1
            writer.close()
            with contextlib.suppress(ConnectionError):
                await writer.wait_closed()

    async def broadcast(self):
        while True:
            await asyncio.sleep(0.05)
            now = time.monotonic()
            for sid,s in list(self.sessions.items()):
                a,b = self.peers.get(s['from']),self.peers.get(s['to'])
                if now >= s['expires']:
                    self.finish(sid,'expired','Interaction timed out.')
                elif not a or not b or (s['status']=='pending' and not self.nearby(a,b,allow_inactive=True)):
                    self.finish(sid,'cancelled','Player moved away or became unavailable.')
            self.update_checkpoints(now)
            self.social.tick()
            self.item_trades.tick()
            self.pokemon_trades.tick()
            rooms = {}
            for peer in list(self.peers.values()):
                state = peer.state if now - peer.updated < 2 else {'active': False}
                rooms.setdefault(peer.room, []).append({'id': peer.id, 'name': peer.name, 'state': state})
            payloads = {room: (json.dumps({'type': 'peers', 'players': players, 'checkpoint': self.checkpoints.get(room,{})}, allow_nan=False) + '\n').encode()
                        for room, players in rooms.items()}
            for peer in list(self.peers.values()):
                if peer.writer.is_closing():
                    continue
                if peer.writer.transport.get_write_buffer_size() > 131072:
                    peer.writer.close()
                    continue
                peer.writer.write(payloads[peer.room])

async def run(host, port, build_version='unknown'):
    relay = PresenceRelay(build_version=build_version)
    server = await asyncio.start_server(relay.client, host, port, limit=MAX_LINE)
    print(f'Presence relay listening on {host}:{port}; Ctrl+C stops it.', flush=True)
    broadcaster = asyncio.create_task(relay.broadcast())
    try:
        async with server:
            await server.serve_forever()
    finally:
        broadcaster.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await broadcaster

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    try:
        from launcher_ui.versioning import current_version
        build_version = current_version()
    except (ImportError, OSError, ValueError, TypeError):
        build_version = 'unknown'
    try:
        asyncio.run(run(args.host, args.port, build_version))
    except KeyboardInterrupt:
        pass
