"""Two-phase item transfers. Durable commit decisions are replayed after reconnect.

The relay never holds bag data or game files. Clients validate their own inventories.
"""
import json
import os
import time
import uuid
from copy import deepcopy
from pathlib import Path

class ItemTrades:
    def __init__(self, relay, path):
        self.relay = relay
        self.path = Path(path)
        self.trades = {}
        self.journal_errors = {}
        if self.path.exists():
            self.trades = json.loads(self.path.read_text(encoding='utf-8'))
            # A prepared transaction has no durable commit decision and is aborted.
            for trade in self.trades.values():
                if trade['status'] in ('offered', 'preparing'):
                    trade['status'] = 'cancelled'
                    trade['reason'] = 'Relay restarted before commit.'
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
            trade.clear(); trade.update(previous)
            raise
    def journal_error(self, trade):
        now = time.monotonic()
        if now-self.journal_errors.get(trade['id'], -10) < 2:
            return
        self.journal_errors[trade['id']] = now
        for peer in self.peers(trade):
            if peer:
                self.relay.send(peer, {'type': 'item_trade_error',
                    'reason': 'Relay cannot save the transfer journal. Free disk space and retry; items remain held.'})
    def peers(self, trade):
        return [next((p for p in self.relay.peers.values()
                      if getattr(p, 'item_client', '') == token and p.room == trade['room']), None)
                for token in (trade['fromClient'], trade['toClient'])]
    def notify(self, trade):
        for index, peer in enumerate(self.peers(trade)):
            if peer:
                self.notify_peer(trade, peer, index)
    def notify_peer(self, trade, peer, index):
        self.relay.send(peer, {k: v for k, v in trade.items()
            if k not in ('fromClient', 'toClient', 'ready', 'acks', 'expires', 'room')} |
            {'type': 'item_trade', 'give': index == 0,
             'localApplied': peer.item_client in trade['acks'],
             'otherApplied': (trade['toClient'] if index == 0 else trade['fromClient']) in trade['acks']})
    def resume(self, peer):
        # Only this identity and room may discover its unfinished decision.
        # Completed/cancelled journals are queried by ID instead of reopening old UI.
        for trade in self.trades.values():
            if (trade['status'] in ('offered', 'preparing', 'committed') and
                peer.room == trade['room'] and peer.item_client in (trade['fromClient'], trade['toClient'])):
                self.notify_peer(trade, peer, int(peer.item_client == trade['toClient']))
    def cancel(self, trade, reason):
        if trade['status'] in ('committed', 'complete'):
            return
        self.transition(trade, status='cancelled', reason=reason)
        self.notify(trade)
    def action(self, peer, message):
        try:
            self.apply_action(peer, message)
        except OSError:
            self.relay.send(peer, {'type': 'item_trade_error',
                'reason': 'Relay cannot save the transfer journal. Free disk space and retry; no new decision was made.'})
    def apply_action(self, peer, message):
        def reject(reason):
            self.relay.send(peer, {'type': 'item_trade_error', 'reason': reason})
        token = getattr(peer, 'item_client', '')
        if not token:
            reject('Update both clients to use item trading.'); return
        action = message.get('action')
        if action == 'offer':
            other = self.relay.peers.get(message.get('target')) if isinstance(message.get('target'), str) else None
            item, quantity, rom = message.get('item'), message.get('quantity'), message.get('rom')
            if (not other or other is peer or not getattr(other, 'item_client', '') or
                not self.relay.nearby(peer, other)):
                reject('Both players must be in the overworld on the same map.'); return
            if (type(item) is not int or not 1 <= item < 639 or type(quantity) is not int or
                not 1 <= quantity <= 999 or not isinstance(rom, str) or len(rom) != 64 or
                any(c not in '0123456789abcdef' for c in rom)):
                reject('Invalid item offer.'); return
            if any(t['status'] in ('offered', 'preparing', 'committed') and
                   (token in (t['fromClient'], t['toClient']) or other.item_client in (t['fromClient'], t['toClient']))
                   for t in self.trades.values()):
                reject('Finish the pending item transfer first.'); return
            if any(peer.id in (s['from'], s['to']) or other.id in (s['from'], s['to']) for s in self.relay.sessions.values()):
                reject('Finish the native interaction first.'); return
            if self.relay.pokemon_trades.busy(token, other.item_client):
                reject('Finish the pending Pokemon trade first.'); return
            trade = dict(id=uuid.uuid4().hex, status='offered', room=peer.room,
                fromClient=token, toClient=other.item_client, fromName=peer.name, toName=other.name,
                item=item, quantity=quantity, rom=rom, ready=[], acks=[], expires=time.monotonic()+30, reason='')
            self.trades[trade['id']] = trade
            try:
                self.persist()
            except OSError:
                del self.trades[trade['id']]
                raise
            self.notify(trade); return
        trade = self.trades.get(message.get('id')) if isinstance(message.get('id'), str) else None
        if not trade or token not in (trade['fromClient'], trade['toClient']) or peer.room != trade['room']:
            reject('Item transfer unavailable.'); return
        if action == 'query':
            self.notify(trade); return
        if action in ('decline', 'cancel', 'failed'):
            if trade['status'] in ('committed', 'complete'):
                # A committed transfer cannot be cancelled. Replay the decision so
                # the client can finish recovery instead of waiting without a reply.
                self.notify(trade)
            else:
                self.cancel(trade, str(message.get('reason', 'Item transfer cancelled.'))[:160])
            return
        if action == 'accept' and trade['status'] == 'offered' and token == trade['toClient']:
            a, b = self.peers(trade)
            if not a or not b or not self.relay.nearby(a, b, allow_busy=True):
                self.cancel(trade, 'Players moved away.'); return
            self.transition(trade, status='preparing', expires=time.monotonic()+15)
            self.notify(trade); return
        if action == 'ready' and trade['status'] == 'preparing':
            a, b = self.peers(trade)
            if (not a or not b or a.writer.is_closing() or b.writer.is_closing() or
                time.monotonic() >= trade['expires'] or not self.relay.nearby(a, b, allow_busy=True)):
                self.cancel(trade, 'Player disconnected, moved away or became unavailable before commit.'); return
            ready = list(trade['ready'])
            if token not in ready:
                ready.append(token)
            if len(ready) == 2:
                # This persisted decision precedes every inventory write.
                self.transition(trade, ready=ready, status='committed')
                self.notify(trade)
            else:
                trade['ready'] = ready
            return
        if action == 'ready' and trade['status'] in ('committed', 'complete'):
            # A lost notification may make a client repeat its prepared vote.
            self.notify(trade); return
        if action == 'applied' and trade['status'] in ('committed', 'complete'):
            acks = list(trade['acks'])
            if token not in acks:
                acks.append(token)
            self.transition(trade, acks=acks, status='complete' if len(acks)==2 else 'committed')
            self.notify(trade); return
        reject('Item transfer is no longer at that step.')
    def tick(self):
        for trade in list(self.trades.values()):
            if trade['status'] not in ('offered', 'preparing'):
                continue
            a, b = self.peers(trade)
            try:
                if not a or not b:
                    self.cancel(trade, 'Player disconnected before commit.')
                elif time.monotonic() >= trade['expires']:
                    self.cancel(trade, 'Item offer timed out.')
                elif not self.relay.nearby(a, b, allow_busy=True):
                    self.cancel(trade, 'Player moved away or entered another activity.')
            except OSError:
                # Keep the broadcaster alive while persistence is unavailable.
                self.journal_error(trade)
