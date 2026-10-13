"""Opt-in co-op follower greetings and battle previews. Copyright (C) 2026 mvq1303.

These messages never enter the native wireless battle stream or edit a save.
"""
import base64
import binascii
import time

class CoopSocial:
    def __init__(self, relay):
        self.relay = relay
        self.watching = {}
        self.last_frame = {}
        self.last_greet = {}

    def stop(self, viewer, reason):
        target = self.watching.pop(viewer, None)
        if not target:
            return
        peer = self.relay.peers.get(viewer)
        if peer:
            self.relay.send(peer, {'type':'coop', 'action':'stopped', 'reason':reason})
        self.notify(target)

    def notify(self, target):
        peer = self.relay.peers.get(target)
        if peer:
            self.relay.send(peer, {'type':'coop', 'action':'viewers',
                'count':sum(value == target for value in self.watching.values())})

    def tick(self):
        now = time.monotonic()
        for viewer, target in list(self.watching.items()):
            a, b = self.relay.peers.get(viewer), self.relay.peers.get(target)
            if (not a or not b or a.room != b.room or now-a.updated >= 2 or now-b.updated >= 2
                    or not b.state.get('shareBattle') or not b.state.get('inBattle')):
                self.stop(viewer, 'Battle preview ended.')
        live = self.relay.peers.keys()
        self.last_frame = {k:v for k,v in self.last_frame.items() if k in live}
        self.last_greet = {k:v for k,v in self.last_greet.items() if k in live}
    def action(self, peer, message):
        now = time.monotonic()
        def error(reason):
            self.relay.send(peer, {'type':'coop', 'action':'error', 'reason':reason})
        action = message.get('action')
        if action == 'greet':
            target=self.relay.peers.get(message.get('target')) if isinstance(message.get('target'),str) else None
            if (not target or target is peer or target.room!=peer.room or now-peer.updated>=2 or now-target.updated>=2
                    or any(not p.state.get('active') or p.state.get('inBattle') or not p.state.get('followerSpecies') for p in (peer,target))
                    or peer.state.get('map')!=target.state.get('map')
                    or abs(peer.state['tileX']-target.state['tileX'])+abs(peer.state['tileZ']-target.state['tileZ'])>2):
                return error('Bring both followers beside each other in the field.')
            if now-self.last_greet.get(peer.id,-10)<3:return error('Wait a moment before greeting again.')
            self.last_greet[peer.id]=now
            for p in (peer,target):self.relay.send(p,{'type':'coop','action':'greet','from':peer.id,'to':target.id,'map':peer.state['map']})
        elif action == 'watch':
            target = self.relay.peers.get(message.get('target')) if isinstance(message.get('target'),str) else None
            if (not target or target is peer or target.room != peer.room
                    or not target.state.get('shareBattle') or not target.state.get('inBattle')
                    or now-target.updated >= 2):
                return error('This player is not sharing a battle.')
            self.stop(peer.id, 'Changed battle preview.')
            self.watching[peer.id] = target.id
            self.relay.send(peer, {'type':'coop', 'action':'watching', 'target':target.id, 'name':target.name})
            self.notify(target.id)
        elif action == 'unwatch':
            self.stop(peer.id, 'Stopped watching.')
        elif action == 'frame':
            if now-self.last_frame.get(peer.id, -10) < .45:
                return
            self.tick()
            viewers = [self.relay.peers[k] for k,v in self.watching.items() if v == peer.id and k in self.relay.peers]
            if not viewers:
                return
            encoded = message.get('jpeg')
            if not isinstance(encoded,str) or len(encoded) > 64000:
                return error('Invalid preview frame.')
            try:
                raw = base64.b64decode(encoded,validate=True)
            except (ValueError,binascii.Error):
                return error('Invalid preview frame.')
            if not raw.startswith(b'\xff\xd8') or not raw.endswith(b'\xff\xd9'):
                return error('Invalid preview image.')
            self.last_frame[peer.id] = now
            for viewer in viewers:
                self.relay.send(viewer, {'type':'coop', 'action':'frame', 'from':peer.id, 'jpeg':encoded})
        else:
            error('Unknown co-op action.')
