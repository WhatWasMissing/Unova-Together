"""Consensual, durable swaps of exact encrypted Gen 5 party records.

The relay persists the swap decision before either client may change its party.
Native clients validate the selected slots again and journal them before ready.
"""
import base64
import binascii
import hashlib
import json
import os
import struct
import time
from copy import deepcopy
from pathlib import Path

RECORD_SIZE = 220
OPEN_STATES = ('selecting', 'confirming', 'preparing', 'committed')


def validate_record(value):
    if not isinstance(value, str) or len(value) != 296:
        raise ValueError('Expected one encrypted 220-byte party record.')
    try:
        record = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError('Invalid party record encoding.') from None
    if len(record) != RECORD_SIZE or base64.b64encode(record).decode('ascii') != value:
        raise ValueError('Invalid party record size or encoding.')
    if struct.unpack_from('<H', record, 4)[0] != 0:
        raise ValueError('Pokemon must be fully encrypted and free of invalid-record flags.')
    checksum = struct.unpack_from('<H', record, 6)[0]
    seed, total = checksum, 0
    for offset in range(8, 136, 2):
        seed = (seed * 0x41C64E6D + 0x6073) & 0xffffffff
        total += struct.unpack_from('<H', record, offset)[0] ^ (seed >> 16)
    if total & 0xffff != checksum:
        raise ValueError('Pokemon record checksum does not match.')
    return hashlib.sha256(record).hexdigest()


def valid_rom(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


class PokemonTrades:
    def __init__(self, relay, path):
        self.relay, self.path = relay, Path(path)
        self.trades, self.journal_errors = {}, {}
        if self.path.exists():
            self.trades = json.loads(self.path.read_text(encoding='utf-8'))
            for trade in self.trades.values():
                if trade['status'] in OPEN_STATES[:-1]:
                    trade['status'] = 'cancelled'
                    trade['reason'] = 'Relay restarted before the swap committed.'

    def persist(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.tmp')
        with temp.open('w', encoding='utf-8') as stream:
            json.dump(self.trades, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, self.path)

    def transition(self, trade, **changes):
        previous = deepcopy(trade)
        trade.update(changes)
        try:
            self.persist()
        except OSError:
            trade.clear()
            trade.update(previous)
            raise

    def peers(self, trade):
        return [next((p for p in self.relay.peers.values()
                      if p.item_client == token and p.room == trade['room']), None)
                for token in (trade['fromClient'], trade['toClient'])]

    def busy(self, *tokens):
        return any(t['status'] in OPEN_STATES and
                   any(token in (t['fromClient'], t['toClient']) for token in tokens)
                   for t in self.trades.values())

    def start(self, session):
        a, b = self.relay.peers[session['from']], self.relay.peers[session['to']]
        if (not a.item_client or not b.item_client or a.item_client == b.item_client or
                not a.pokemon_trading or not b.pokemon_trading):
            raise ValueError('Both players need the updated Pokemon trading client.')
        if self.busy(a.item_client, b.item_client):
            raise ValueError('Finish the pending Pokemon trade first.')
        trade = dict(id=session['id'], room=a.room, fromClient=a.item_client, toClient=b.item_client,
                     fromName=a.name, toName=b.name, status='selecting', selections=[None, None],
                     rom='', confirmed=[], ready=[], acks=[], revision=0,
                     expires=time.monotonic()+120, reason='')
        self.trades[trade['id']] = trade
        try:
            self.persist()
        except OSError:
            del self.trades[trade['id']]
            raise
        return trade

    def notify_peer(self, trade, peer, index):
        own, other = trade['selections'][index], trade['selections'][1-index]
        own_token = trade['fromClient'] if index == 0 else trade['toClient']
        other_token = trade['toClient'] if index == 0 else trade['fromClient']
        result = {key: trade[key] for key in ('id', 'status', 'fromName', 'toName', 'rom', 'revision', 'reason')}
        result.update(type='pokemon_trade', localConfirmed=own_token in trade['confirmed'],
                      otherConfirmed=other_token in trade['confirmed'],
                      localReady=own_token in trade['ready'], otherReady=other_token in trade['ready'],
                      localApplied=own_token in trade['acks'], otherApplied=other_token in trade['acks'])
        for prefix, selection in (('local', own), ('other', other)):
            if selection:
                for key in ('slot', 'record', 'hash'):
                    result[prefix+key.capitalize()] = selection[key]
        self.relay.send(peer, result)

    def notify(self, trade):
        for index, peer in enumerate(self.peers(trade)):
            if peer:
                self.notify_peer(trade, peer, index)

    def resume(self, peer):
        for trade in self.trades.values():
            if (trade['status'] in OPEN_STATES and peer.room == trade['room'] and
                    peer.item_client in (trade['fromClient'], trade['toClient'])):
                self.notify_peer(trade, peer, int(peer.item_client == trade['toClient']))

    def end_interaction(self, trade, status, reason=''):
        session = self.relay.sessions.pop(trade['id'], None)
        if session:
            self.relay.notify_session(session, status, reason)

    def cancel(self, trade, reason):
        if trade['status'] in ('committed', 'complete'):
            return
        self.transition(trade, status='cancelled', reason=reason)
        self.end_interaction(trade, 'cancelled', reason)
        self.notify(trade)

    def error(self, peer, reason):
        self.relay.send(peer, {'type': 'pokemon_trade_error', 'reason': reason})

    def action(self, peer, message):
        try:
            self.apply_action(peer, message)
        except OSError:
            self.error(peer, 'Relay cannot save the trade journal. No new swap decision was made; retry.')

    def apply_action(self, peer, message):
        trade = self.trades.get(message.get('id')) if isinstance(message.get('id'), str) else None
        token = peer.item_client
        if not trade or not token or token not in (trade['fromClient'], trade['toClient']) or peer.room != trade['room']:
            self.error(peer, 'Pokemon trade unavailable.'); return
        action = message.get('action')
        if action == 'query':
            self.notify(trade); return
        if action in ('cancel', 'decline', 'failed'):
            if trade['status'] in ('committed', 'complete'):
                self.notify(trade)
            else:
                self.cancel(trade, str(message.get('reason', 'Pokemon trade cancelled.'))[:160])
            return
        index = int(token == trade['toClient'])
        if action == 'select' and trade['status'] in ('selecting', 'confirming'):
            slot, rom, encoded = message.get('slot'), message.get('rom'), message.get('record')
            if type(slot) is not int or not 0 <= slot < 6 or not valid_rom(rom):
                self.error(peer, 'Invalid party slot or ROM identity.'); return
            try:
                digest = validate_record(encoded)
            except ValueError as error:
                self.error(peer, str(error)); return
            other = trade['selections'][1-index]
            if other and rom != other['rom']:
                self.error(peer, 'Both players must use exactly the same ROM version.'); return
            selection = dict(slot=slot, record=encoded, hash=digest, rom=rom)
            if trade['selections'][index] == selection:
                self.notify(trade); return
            selections = deepcopy(trade['selections'])
            selections[index] = selection
            self.transition(trade, selections=selections, rom=rom, confirmed=[], ready=[],
                            revision=trade['revision']+1,
                            status='confirming' if all(selections) else 'selecting',
                            expires=time.monotonic()+120)
            self.notify(trade); return
        if action in ('confirm', 'ready') and trade['status'] in ('committed', 'complete'):
            self.notify(trade); return
        if action == 'confirm' and trade['status'] == 'preparing' and token in trade['confirmed']:
            own, other = trade['selections'][index], trade['selections'][1-index]
            if message.get('localHash') == own['hash'] and message.get('otherHash') == other['hash']:
                self.notify(trade); return
        required = 'confirming' if action == 'confirm' else 'preparing' if action == 'ready' else None
        if required and trade['status'] == required:
            own, other = trade['selections'][index], trade['selections'][1-index]
            if (not own or not other or message.get('localHash') != own['hash'] or
                    message.get('otherHash') != other['hash']):
                self.error(peer, 'Pokemon selection changed. Review both Pokemon and confirm again.'); return
            a, b = self.peers(trade)
            if (not a or not b or a.writer.is_closing() or b.writer.is_closing() or
                    time.monotonic() >= trade['expires'] or
                    not self.relay.nearby(a, b, allow_busy=True, allow_inactive=True)):
                self.cancel(trade, 'Player disconnected, moved away or became unavailable before commit.'); return
            key = 'confirmed' if action == 'confirm' else 'ready'
            votes = list(trade[key])
            if token not in votes:
                votes.append(token)
            changes = {key: votes}
            if len(votes) == 2:
                changes.update(status='preparing' if action == 'confirm' else 'committed',
                               expires=time.monotonic()+20)
            self.transition(trade, **changes)
            # The committed notification occurs only after fsync + atomic replace.
            self.notify(trade); return
        if action == 'applied' and trade['status'] in ('committed', 'complete'):
            acks = list(trade['acks'])
            if token not in acks:
                acks.append(token)
            self.transition(trade, acks=acks, status='complete' if len(acks) == 2 else 'committed')
            if len(acks) == 2:
                self.end_interaction(trade, 'complete')
            self.notify(trade); return
        self.error(peer, 'Pokemon trade is no longer at that step.')

    def tick(self):
        for trade in list(self.trades.values()):
            if trade['status'] not in OPEN_STATES[:-1]:
                continue
            a, b = self.peers(trade)
            try:
                if not a or not b:
                    self.cancel(trade, 'Player disconnected before commit.')
                elif time.monotonic() >= trade['expires']:
                    self.cancel(trade, 'Pokemon trade timed out.')
                elif not self.relay.nearby(a, b, allow_busy=True, allow_inactive=True):
                    self.cancel(trade, 'Player moved away or entered another activity.')
            except OSError:
                now = time.monotonic()
                if now-self.journal_errors.get(trade['id'], -10) >= 2:
                    self.journal_errors[trade['id']] = now
                    for peer in self.peers(trade):
                        if peer:
                            self.error(peer, 'Relay cannot save the trade journal. Pokemon remain unchanged.')
