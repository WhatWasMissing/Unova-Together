"""Loopback protocol tests; no ROM, emulator, or external network required."""
import asyncio
import contextlib
import json
import unittest
import tempfile
from pathlib import Path
from presence_server import PresenceRelay, validate_state

def state(sequence=1, active=True, **changes):
    data = {'type': 'state', 'sequence': sequence, 'active': active,
            'map': 1029, 'tileX': 416, 'tileZ': 466, 'smoothX': 415.5,
            'smoothZ': 466, 'facing': 'East', 'moving': True}
    data.update(changes)
    return data

class PreviewQueueTests(unittest.TestCase):
    def test_sprite_and_compatibility_metadata(self):
        values=dict(followerGender=1,followerShiny=True,coopProtocol=2,modVersion='1.0.7-dev',romFingerprint='a'*64)
        result=validate_state(state(**values),0)
        for key,value in values.items():self.assertEqual(result[key],value)
        for key,value in (('followerGender',3),('followerShiny',1),('coopProtocol',True),('modVersion','bad\nversion'),('romFingerprint','x'*64)):
            with self.subTest(key=key),self.assertRaises(ValueError):validate_state(state(**{key:value}),0)

    def test_slow_viewer_drops_preview_without_closing_presence(self):
        from types import SimpleNamespace
        writes=[];closed=[]
        writer=SimpleNamespace(is_closing=lambda:False,
            transport=SimpleNamespace(get_write_buffer_size=lambda:40000),
            write=writes.append,close=lambda:closed.append(True))
        peer=SimpleNamespace(writer=writer)
        PresenceRelay.send(None,peer,{'type':'coop','action':'frame','jpeg':'fixture'})
        self.assertEqual(writes,[]);self.assertEqual(closed,[])
        PresenceRelay.send(None,peer,{'type':'coop','action':'stopped'})
        self.assertEqual(len(writes),1);self.assertEqual(closed,[])

class RelayTests(unittest.IsolatedAsyncioTestCase):
    async def test_coop_preview_subscription_over_real_socket(self):
        import base64
        a,aw,aid=await self.join('Watcher')
        b,bw,bid=await self.join('Battler')
        await self.send(aw,state(1,inBattle=False))
        await self.send(bw,state(1,inBattle=True,shareBattle=True,coopStatus='battle'))
        await self.snapshot(a,lambda players:any(p['id']==bid and p['state'].get('shareBattle') for p in players))
        await self.send(aw,{'type':'coop','action':'watch','target':bid})
        async def coop(reader,action):
            while True:
                data=json.loads(await asyncio.wait_for(reader.readline(),2))
                if data.get('type')=='coop' and data.get('action')==action:return data
        self.assertEqual((await coop(a,'watching'))['target'],bid)
        self.assertEqual((await coop(b,'viewers'))['count'],1)
        encoded=base64.b64encode(b'\xff\xd8fixture\xff\xd9').decode()
        await self.send(bw,{'type':'coop','action':'frame','jpeg':encoded})
        self.assertEqual((await coop(a,'frame'))['jpeg'],encoded)
        await self.send(bw,state(2,inBattle=False,shareBattle=True))
        self.assertEqual((await coop(a,'stopped'))['action'],'stopped')
    async def test_follower_metadata_is_optional_and_bounded(self):
        self.assertNotIn('followerSpecies',validate_state(state(),0))
        self.assertEqual(validate_state(state(followerSpecies=649,followerForm=31),0)['followerSpecies'],649)
        for value in (True,-1,650,1.5,'25'):
            with self.assertRaises(ValueError): validate_state(state(followerSpecies=value),0)
        with self.assertRaises(ValueError): validate_state(state(followerForm=32),0)

    async def test_field_zone_is_forwarded_for_teleport(self):
        a,wa,aid,b,wb,bid=await self.active_pair()
        await self.send(wa,state(2,fieldZone=0))
        players=await self.snapshot(b,lambda ps:any(p['id']==aid and p['state'].get('fieldZone')==0 for p in ps))
        self.assertEqual(next(p['state'] for p in players if p['id']==aid)['fieldZone'],0)
    async def test_menu_flag_is_typed_and_retained(self):
        self.assertTrue(validate_state(state(inMenu=True, moving=False),0)['inMenu'])
        self.assertFalse(validate_state(state(inMenu=False),0)['inMenu'])
        self.assertNotIn('inMenu',validate_state(state(),0))
        with self.assertRaises(ValueError): validate_state(state(inMenu=1),0)
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pokeplay-presence-test-')
        self.relay = PresenceRelay(Path(self.temp.name)/'item-transfers.json')
        self.server = await asyncio.start_server(self.relay.client,'127.0.0.1',0,limit=4096)
        self.port = self.server.sockets[0].getsockname()[1]
        self.broadcast = asyncio.create_task(self.relay.broadcast())
        self.writers = []

    async def asyncTearDown(self):
        for writer in self.writers:
            writer.close()
            with contextlib.suppress(ConnectionError): await writer.wait_closed()
        self.server.close(); await self.server.wait_closed()
        self.broadcast.cancel()
        with contextlib.suppress(asyncio.CancelledError): await self.broadcast
        await asyncio.sleep(0)
        self.temp.cleanup()

    async def join(self, name, room='test', interactions=True):
        reader, writer = await asyncio.open_connection('127.0.0.1',self.port)
        self.writers.append(writer)
        writer.write((json.dumps({'type':'join','version':1,'name':name,'room':room,'interactions':interactions,'overworldBattles':True})+'\n').encode())
        await writer.drain()
        welcome = json.loads(await asyncio.wait_for(reader.readline(),1))
        self.assertEqual(welcome['type'],'welcome')
        self.assertTrue(welcome.get('fieldZonePresence'))
        return reader,writer,welcome['id']

    async def snapshot(self, reader, predicate):
        async def wait():
            while True:
                line=await reader.readline()
                self.assertTrue(line)
                data=json.loads(line)
                if data['type']=='peers' and predicate(data['players']):return data['players']
        return await asyncio.wait_for(wait(),2)

    async def event(self, reader, event_type, status=None):
        async def wait():
            while True:
                data = json.loads(await reader.readline())
                if data.get('type') == event_type and (status is None or data.get('status') == status):
                    return data
        return await asyncio.wait_for(wait(),2)

    async def send(self, writer, message):
        writer.write((json.dumps(message)+'\n').encode()); await writer.drain()

    async def active_pair(self):
        a,wa,aid=await self.join('A'); b,wb,bid=await self.join('B')
        await self.send(wa,state()); await self.send(wb,state())
        await self.snapshot(a,lambda ps:len(ps)==2 and all(p['state'].get('active') for p in ps))
        return a,wa,aid,b,wb,bid

    async def test_request_accept_cancel_and_authorization(self):
        a,wa,aid,b,wb,bid=await self.active_pair()
        c,wc,cid=await self.join('C')
        await self.send(wa,{'type':'interaction','action':'request','kind':'trade','target':bid})
        pending=await self.event(b,'interaction','pending'); sid=pending['id']
        self.assertEqual(pending['from'],aid); self.assertEqual(pending['to'],bid)
        await self.event(a,'interaction','pending')
        for writer,reader in [(wa,a),(wc,c)]:
            await self.send(writer,{'type':'interaction','action':'accept','id':sid})
            await self.event(reader,'interaction_error')
        self.assertEqual(self.relay.sessions[sid]['status'],'pending')
        await self.send(wb,{'type':'interaction','action':'accept','id':sid})
        await self.event(a,'interaction','accepted'); await self.event(b,'interaction','accepted')
        await self.send(wa,{'type':'interaction','action':'cancel','id':sid})
        await self.event(a,'interaction','cancelled'); await self.event(b,'interaction','cancelled')
        self.assertFalse(self.relay.sessions)

    async def test_decline_timeout_and_disconnect(self):
        a,wa,aid,b,wb,bid=await self.active_pair()
        async def request():
            self.relay.peers[aid].last_request=-10
            await self.send(wa,{'type':'interaction','action':'request','kind':'battle','target':bid})
            await self.event(a,'interaction','pending')
            return (await self.event(b,'interaction','pending'))['id']
        sid=await request()
        await self.send(wb,{'type':'interaction','action':'decline','id':sid})
        await self.event(a,'interaction','declined'); await self.event(b,'interaction','declined')
        sid=await request(); self.relay.sessions[sid]['expires']=0
        await self.event(a,'interaction','expired'); await self.event(b,'interaction','expired')
        sid=await request()
        wa.close(); await wa.wait_closed()
        await self.event(b,'interaction','cancelled'); self.assertFalse(self.relay.sessions)

    async def test_room_map_capability_busy_and_rate_limits(self):
        a,wa,aid,b,wb,bid=await self.active_pair()
        c,wc,cid=await self.join('C','other'); old,wo,oid=await self.join('Old',interactions=False)
        async def request(target, reader=a, writer=wa):
            await self.send(writer,{'type':'interaction','action':'request','kind':'trade','target':target})
            return await self.event(reader,'interaction_error')
        for target in [cid,oid,aid]:
            self.relay.peers[aid].last_request=-10
            await request(target)
        self.relay.peers[aid].last_request=-10
        await self.send(wb,state(2,map=1030,tileX=425,smoothX=425))
        await self.snapshot(a,lambda ps:any(p['id']==bid and p['state'].get('tileX')==425 for p in ps))
        await request(bid)
        await self.send(wb,state(3)); self.relay.peers[aid].last_request=-10
        await self.snapshot(a,lambda ps:any(p['id']==bid and p['state'].get('sequence')==3 for p in ps))
        await self.send(wa,{'type':'interaction','action':'request','kind':'trade','target':bid})
        pending=await self.event(a,'interaction','pending'); await self.event(b,'interaction','pending')
        await request(bid) # Sender cooldown.
        await request(aid,b,wb) # Recipient already busy.
        self.assertEqual(len(self.relay.sessions),1)
        await self.send(wb,state(4,False))
        await self.event(a,'interaction','cancelled'); self.assertFalse(self.relay.sessions)

    async def test_two_players_pause_and_room_isolation(self):
        a,wa,aid=await self.join('A')
        b,wb,bid=await self.join('B')
        c,wc,cid=await self.join('C','other')
        wa.write((json.dumps(state())+'\n').encode()); await wa.drain()
        roster=await self.snapshot(b,lambda ps:any(p['id']==aid and p['state'].get('active') for p in ps))
        self.assertEqual({p['id'] for p in roster},{aid,bid})
        remote=next(p for p in roster if p['id']==aid)
        self.assertEqual(remote['state']['smoothX'],415.5)
        self.assertNotIn('type',remote['state'])
        isolated=await self.snapshot(c,lambda ps:len(ps)==1)
        self.assertEqual(isolated[0]['id'],cid)
        wa.write((json.dumps(state(2,False))+'\n').encode()); await wa.drain()
        await self.snapshot(b,lambda ps:any(p['id']==aid and not p['state'].get('active') for p in ps))
        wa.close(); await wa.wait_closed()
        await self.snapshot(b,lambda ps:all(p['id']!=aid for p in ps))

    async def test_battle_flag_forwarding_blocks_requests_and_clears(self):
        a,wa,aid,b,wb,bid=await self.active_pair()
        await self.send(wa,state(2,inBattle=True,moving=False))
        ps=await self.snapshot(b,lambda ps:any(p['id']==aid and p['state'].get('inBattle') for p in ps))
        battle=next(p['state'] for p in ps if p['id']==aid)
        self.assertEqual(battle['map'],1029); self.assertFalse(battle['moving'])
        await self.send(wb,{'type':'interaction','action':'request','kind':'trade','target':aid})
        await self.event(b,'interaction_error'); self.assertFalse(self.relay.sessions)
        await self.send(wa,state(3,inBattle=False))
        await self.snapshot(b,lambda ps:any(p['id']==aid and p['state'].get('inBattle') is False for p in ps))
        wa.close(); await wa.wait_closed()
        await self.snapshot(b,lambda ps:all(p['id']!=aid for p in ps))

    async def test_battle_partner_leaves_and_returns_without_replacing_anchor(self):
        a,wa,aid,b,wb,bid=await self.active_pair()
        await self.send(wa,state(2,map=439,inBattle=True,moving=False))
        await self.snapshot(b,lambda ps:any(p['id']==aid and p['state'].get('inBattle') for p in ps))
        for sequence,map_id in ((2,440),(3,439)):
            await self.send(wb,state(sequence,map=map_id,inBattle=False))
            ps=await self.snapshot(a,lambda ps:any(p['id']==bid and p['state'].get('map')==map_id for p in ps))
            self.assertEqual(next(p['state'] for p in ps if p['id']==bid)['map'],map_id)
            self.assertEqual(self.relay.peers[aid].state['map'],439)
            self.assertTrue(self.relay.peers[aid].state['inBattle'])
        await self.send(wa,state(3,map=439,inBattle=False))
        await self.snapshot(b,lambda ps:any(p['id']==aid and p['state'].get('inBattle') is False and p['state'].get('map')==439 for p in ps))

    async def test_invalid_state_disconnect_and_stale_state(self):
        a,wa,aid=await self.join('A')
        b,wb,bid=await self.join('B')
        wa.write((json.dumps(state())+'\n').encode()); await wa.drain()
        await self.snapshot(b,lambda ps:any(p['id']==aid and p['state'].get('active') for p in ps))
        self.relay.peers[aid].updated-=3
        await self.snapshot(b,lambda ps:any(p['id']==aid and not p['state'].get('active') for p in ps))
        wa.write((json.dumps(state(2,smoothX=float('nan')))+'\n').encode()); await wa.drain()
        await self.snapshot(b,lambda ps:all(p['id']!=aid for p in ps))

    async def checkpoint_snapshot(self, reader, predicate):
        async def wait():
            while True:
                data=json.loads(await reader.readline())
                if data.get('type')=='peers' and predicate(data.get('checkpoint',{})): return data['checkpoint']
        return await asyncio.wait_for(wait(),2)

    async def test_checkpoint_arrival_battle_and_completion(self):
        a,wa,aid,b,wb,bid=await self.active_pair()
        await self.send(wb,state(2,smoothX=420,tileX=420))
        await self.send(wa,{'type':'checkpoint','action':'create','target':bid})
        challenge=await self.checkpoint_snapshot(a,lambda c:c.get('status')=='active')
        self.assertEqual(challenge['participants'],[aid,bid])
        self.assertEqual(challenge['arrived'],[aid])
        await self.send(wb,state(3,inBattle=True))
        await asyncio.sleep(.1)
        self.assertEqual(self.relay.checkpoints['test']['status'],'active')
        await self.send(wb,state(4,map=1030))
        await asyncio.sleep(.1)
        self.assertEqual(self.relay.checkpoints['test']['status'],'active')
        await self.send(wb,state(5))
        done=await self.checkpoint_snapshot(a,lambda c:c.get('status')=='complete')
        self.assertEqual(set(done['arrived']),{aid,bid})

    async def test_checkpoint_isolation_cancellation_and_disconnect(self):
        a,wa,aid,b,wb,bid=await self.active_pair()
        c,wc,cid=await self.join('C','other')
        await self.send(wb,state(2,smoothX=420,tileX=420))
        await self.send(wa,{'type':'checkpoint','action':'create','target':cid})
        await self.event(a,'checkpoint_error')
        await self.send(wa,{'type':'checkpoint','action':'create','target':bid})
        await self.checkpoint_snapshot(a,lambda c:c.get('status')=='active')
        await self.send(wc,{'type':'checkpoint','action':'cancel'})
        await asyncio.sleep(.1)
        self.assertEqual(self.relay.checkpoints['test']['status'],'active')
        self.assertNotIn('other',self.relay.checkpoints)
        wb.close(); await wb.wait_closed()
        await self.checkpoint_snapshot(a,lambda c:c.get('status')=='cancelled')

    async def test_checkpoint_stale_and_participant_cancel(self):
        a,wa,aid,b,wb,bid=await self.active_pair()
        await self.send(wb,state(2,smoothX=420,tileX=420))
        await self.send(wa,{'type':'checkpoint','action':'create','target':bid})
        await self.checkpoint_snapshot(a,lambda c:c.get('status')=='active')
        self.relay.peers[bid].state=validate_state(state(3),2)
        self.relay.peers[bid].updated-=3
        await asyncio.sleep(.1)
        self.assertEqual(self.relay.checkpoints['test']['status'],'active')
        await self.send(wb,{'type':'checkpoint','action':'cancel'})
        await self.checkpoint_snapshot(a,lambda c:c.get('status')=='cancelled')

class StateTests(unittest.TestCase):
    def test_sequence_and_bounds(self):
        self.assertEqual(validate_state(state(),0)['smoothX'],415.5)
        for changes in [dict(sequence=0),dict(sequence=True),dict(map=0),dict(smoothX=99999),
                        dict(smoothZ=float('inf')),dict(facing='invalid'),dict(tileX=400),dict(inBattle=1)]:
            with self.assertRaises(ValueError):validate_state(state(**changes),0)
        self.assertEqual(validate_state({'sequence':2,'active':False,'extra':'ignored'},1),
                         {'sequence':2,'active':False})

    def test_field_zone_is_optional_bounded_and_sentinel_is_omitted(self):
        self.assertEqual(validate_state(state(fieldZone=0),0)['fieldZone'],0)
        self.assertEqual(validate_state(state(fieldZone=65534),0)['fieldZone'],65534)
        self.assertNotIn('fieldZone',validate_state(state(fieldZone=-1),0))
        self.assertNotIn('fieldZone',validate_state(state(fieldZone=65535),0))
        for value in (True,-2,65536,1.5,'4'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                validate_state(state(fieldZone=value),0)

if __name__=='__main__':unittest.main()
