"""Exercise real native launcher pages with disposable data; no game is launched."""
from pathlib import Path
import argparse, io, json, hashlib, tempfile, time, threading, unittest, zipfile
from unittest.mock import patch, MagicMock
from PIL import ImageGrab
from launcher_ui.app import Launcher
from launcher_ui.components import HERE, THEME
import unova_updater as u

OUTPUT=None

class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.home=Path(self.temp.name)
        game=self.home/'builds/current';game.mkdir(parents=True)
        (game/'melonDS.exe').write_bytes(b'not a real executable');(game/'VERSION.txt').write_text('0.3.5')
        (game/'melonDS.toml').write_text('# private controls\n')
        self.rom=self.home/'fixture.nds';self.rom.write_bytes(b'disposable ROM placeholder')
        self.app=Launcher(self.home,testing=True);self.app._open_mod('black2',save=False);self.app.update_idletasks();self.app.update()
    def tearDown(self):
        self.app.destroy();self.temp.cleanup()
    def wait(self,timeout=5):
        deadline=time.monotonic()+timeout
        while self.app.busy and time.monotonic()<deadline:self.app.update();time.sleep(.01)
        self.app.update();self.assertFalse(self.app.busy)
    def feed(self,v='0.3.6'):
        base=f'https://github.com/{u.REPO}/releases/download/v{v}/'
        return {'release':{'version':v,'numbers':u.version(v),'name':f'Unova-Together-{v}-Windows-x64.zip','size':100,'url':base+'release.zip','sums':base+'sums.txt'},
                'news':u.release_news([{'tag_name':'v'+v,'name':'Official release '+v,'body':'## Changes\nReal release notes.','published_at':'2026-10-08'}])}
    def test_game_selection_keeps_ds_rom_and_profiles_separate(self):
        from launcher_ui import game_routes
        self.app.rom.set(str(self.rom));profile=self.app.active_profile_id
        self.app.selected_game.set(game_routes.GAMES['pokemon-x']);self.app._game_selected();self.app.update()
        self.assertTrue(self.app.research_card.winfo_viewable());self.assertFalse(self.app.ds_game_card.winfo_viewable())
        self.assertEqual(self.app.rom.get(),str(self.rom));self.assertEqual(self.app.active_profile_id,profile)
        stored=json.loads(self.app.config_path.read_text());self.assertEqual(stored['selected_game'],game_routes.GAMES['pokemon-x'])
        if OUTPUT:
            self.app.attributes('-topmost',True);self.app.lift();self.app.update();time.sleep(.2)
            x,y=self.app.winfo_rootx(),self.app.winfo_rooty();w,h=self.app.winfo_width(),self.app.winfo_height()
            ImageGrab.grab(bbox=(x,y,x+w,y+h)).save(OUTPUT/'pokemon-x.png')
        self.app.selected_game.set(game_routes.GAMES['black2']);self.app._game_selected();self.app.update()
        self.assertTrue(self.app.ds_game_card.winfo_viewable());self.assertFalse(self.app.research_card.winfo_viewable())

    def test_library_is_startup_even_after_last_mod_was_saved(self):
        from launcher_ui import game_routes
        self.app.selected_game.set(game_routes.GAMES['pokemon-x']);self.app._save();self.app.destroy()
        with patch.object(Launcher,'check') as check,patch.object(Launcher,'refresh_guides') as refresh:
            self.app=Launcher(self.home,testing=True);self.app.update()
            self.assertEqual(self.app.page_name,'Library');self.assertIsNone(self.app.active_mod)
            self.assertEqual(self.app.visible_pages,('Library',));check.assert_not_called();refresh.assert_not_called()
            self.assertEqual(set(self.app.library_buttons),{'black2','pokemon-x'})
            if OUTPUT:
                self.app.attributes('-topmost',True);self.app.lift();self.app.update();time.sleep(.2)
                x,y=self.app.winfo_rootx(),self.app.winfo_rooty()
                ImageGrab.grab(bbox=(x,y,x+self.app.winfo_width(),y+self.app.winfo_height())).save(OUTPUT/'mod-library.png')

    def test_library_routes_hide_other_mod_pages_and_guard_cross_mod_navigation(self):
        self.app._return_library();self.app.library_buttons['pokemon-x'].invoke();self.app.update()
        self.assertEqual(self.app.page_name,'XPlay');self.assertTrue(self.app.research_card.winfo_ismapped())
        self.assertFalse(self.app.nav['Settings'].winfo_ismapped());self.assertFalse(self.app.nav['Updates'].winfo_ismapped())
        self.app.show_page('Profiles');self.assertEqual(self.app.page_name,'XPlay')
        self.app._cycle_page(1);self.assertEqual(self.app.page_name,'XCoop')
        self.app._controller_action('back');self.assertEqual(self.app.page_name,'XPlay')
        self.app._controller_action('back');self.assertEqual(self.app.page_name,'Library')
        self.app.library_buttons['black2'].invoke();self.app.update()
        self.assertEqual(self.app.page_name,'Play');self.assertTrue(self.app.nav['Settings'].winfo_ismapped())
        self.assertFalse(self.app.nav['XCoop'].winfo_ismapped())

    def test_mod_switch_waits_for_active_operation_and_missing_x_setup_is_recoverable(self):
        self.app.busy=True;self.app._open_mod('pokemon-x');self.assertEqual(self.app.active_mod,'black2')
        self.app.busy=False;self.app._open_mod('pokemon-x');self.app.research_root.set(str(self.home/'missing'))
        self.app._launch_research();self.assertIn('Choose the prepared',self.app.status.get())
        self.assertFalse(self.app.busy);self.app._return_library();self.assertEqual(self.app.page_name,'Library')

    def test_selected_3ds_game_dispatches_its_adapter_without_ds_settings(self):
        from launcher_ui import game_routes
        self.app.selected_game.set(game_routes.GAMES['pokemon-x'])
        with patch.object(self.app,'_launch_research') as launch:
            self.app.launch();launch.assert_called_once_with(None)
            launch.reset_mock();self.app._start_lan('host');launch.assert_called_once_with('host')

    def test_simple_save_slots_auto_save_and_keep_existing_data(self):
        self.app.rom.set(str(self.rom));self.app.show_page('Profiles');self.app.update()
        self.assertFalse(self.app.profile_advanced_visible);self.assertIn('No save yet',self.app.save_summary.get())
        self.app.profile_label.set('My adventure')
        stored=json.loads(self.app.config_path.read_text())['profiles'][0]
        self.assertEqual(stored['label'],'My adventure');self.assertIn('My adventure',self.app.active_slot.get())
        self.rom.with_suffix('.save').write_bytes(b'first slot save');self.app.show_page('Profiles');self.app._backup_now()
        self.assertIn('Manual backup',self.app.backup_picker.get());self.assertEqual(str(self.app.restore_button['state']),'normal')
        first=self.app.active_profile_id;self.app._new_profile()
        self.assertEqual(self.app.rom.get(),str(self.rom));self.assertNotEqual(first,self.app.active_profile_id)
        self.assertEqual(self.app.backup_paths,[]);self.assertIn('play-profiles',self.app.save_dir.get())
        self.app.profile_label.set('Second adventure');self.app._toggle_profile_advanced();self.app.update()
        self.assertTrue(self.app.profile_advanced_visible);self.app._toggle_profile_advanced()
        self.app.profile_picker.current(0);self.app._select_profile()
        self.assertEqual(self.app.profile_label.get(),'My adventure');self.assertTrue(self.app.backup_paths)
        self.assertEqual(self.rom.with_suffix('.save').read_bytes(),b'first slot save')

    def test_open_backups_reports_folder_creation_failure(self):
        with patch('launcher_ui.app.Path.mkdir',side_effect=PermissionError('read-only folder')):
            self.app._open_backups()
        self.assertIn('Could not open backups folder',self.app.status.get())
        self.assertIn('read-only folder',self.app.status.get())

    def test_player_model_preference_persists_and_keeps_save_folder_with_source_rom(self):
        from launcher_ui import preferences as prefs, services
        self.app.preference_values['player_model']=4715;self.app._save()
        item=self.app._active_profile()
        self.assertEqual(services.normalize(item)['preferences']['player_model'],4715)
        self.app._apply_save_folder(self.home/'builds/current',item,default_directory=self.rom.parent)
        document=prefs.read_document(self.home/'builds/current')
        self.assertEqual(Path(document['Instance0']['SaveFilePath']).resolve(),self.rom.parent.resolve())
    def test_mega_feature_plays_supplied_mawile_front_and_back_gifs(self):
        from PIL import Image
        assets=HERE/'assets/features'
        for filename in ('mega-mawile-front.gif','mega-mawile-back.gif'):
            with Image.open(assets/filename) as gif:
                self.assertEqual(gif.n_frames,72)
                gif.seek(0);self.assertEqual(gif.info.get('duration'),80)
        self.app.show_page('Features');self.app.update()
        self.assertEqual(len(self.app.feature_mega_frames),2)
        self.assertEqual([len(frames) for frames in self.app.feature_mega_frames],[72,72])
        frame=self.app.feature_mega_frame
        self.assertEqual([widget.cget('image') for widget in self.app.feature_mega_labels],
                         [str(frames[frame]) for frames in self.app.feature_mega_frames])
        time.sleep(.1);self.app.update()
        frame=(frame+1)%72;self.assertEqual(self.app.feature_mega_frame,frame)
        self.assertEqual([widget.cget('image') for widget in self.app.feature_mega_labels],
                         [str(frames[frame]) for frames in self.app.feature_mega_frames])
        self.app.show_page('Play');frame=self.app.feature_mega_frame
        time.sleep(.1);self.app.update();self.assertEqual(self.app.feature_mega_frame,frame)
    def test_cleanup_button_prunes_owned_files_and_keeps_save(self):
        import unova_storage as storage
        base=self.home/'.updates/versions'
        for version in ('1.0.1','1.0.2','1.0.3'):
            root=base/version/'Unova-Together';(root/'builds/current').mkdir(parents=True)
            (root/'builds/current/melonDS.exe').write_bytes(b'fixture');(root/'builds/current/VERSION.txt').write_text(version)
            storage.record_package(root)
        (self.home/'.updates/active.json').write_text('{"version":"1.0.3"}')
        self.app.root=base/'1.0.3/Unova-Together'
        old=base/'1.0.1/Unova-Together';(old/'Redux.save').write_bytes(b'private save')
        with patch.object(storage,'running_paths',return_value=[]):
            self.app.cleanup_button.invoke();self.wait()
        self.assertIn('Cleaned 1 old build',self.app.preflight_text.get('1.0','end'))
        self.assertEqual((old/'Redux.save').read_bytes(),b'private save');self.assertFalse((old/'builds/current/melonDS.exe').exists())

    def test_corrupt_backup_shows_recoverable_error(self):
        item=self.app._active_profile();folder=self.home/'save-backups'/item['id'];folder.mkdir(parents=True)
        archive=folder/'malformed.zip'
        with zipfile.ZipFile(archive,'w') as bundle:
            bundle.writestr('fixture.sav',b'not restored');bundle.writestr('manifest.json','[]')
        self.app.backup_paths=[archive];self.app.backup_picker['values']=['Malformed backup'];self.app.backup_picker.current(0)
        with patch('launcher_ui.app.prefs.any_running',return_value=False):self.app._restore_backup()
        self.assertEqual(self.app.status.get(),'Invalid backup manifest.')

    def test_pages_keyboard_and_small_window(self):
        self.assertTrue(self.app.news);self.assertGreaterEqual(len(self.app.images),4)
        for size in ('1040x760','860x660'):
            self.app.geometry(size);self.app.update()
            for page in ('Play','Profiles','Co-op','Features','News','Updates','Settings','Tools','Setup'):
                self.app.show_page(page);self.app.update()
                self.assertTrue(self.app.pages[page].winfo_ismapped())
                self.assertGreater(self.app.nav[page].winfo_height(),20)
                self.assertLessEqual(self.app.nav[page].winfo_rooty()+self.app.nav[page].winfo_height(),self.app.winfo_rooty()+self.app.winfo_height())
                self.assertEqual(self.app.title(),'Pokemon Together · Unova Together · '+('Games & saves' if page=='Profiles' else page))
                visible_actions={'Play':self.app.play,'News':self.app.news_link,'Updates':self.app.cancel_button}
                if page in visible_actions:
                    w=visible_actions[page];self.assertGreater(w.winfo_height(),25)
                    self.assertLessEqual(w.winfo_rooty()+w.winfo_height(),self.app.winfo_rooty()+self.app.winfo_height())
                    self.assertLessEqual(w.winfo_rootx()+w.winfo_width(),self.app.winfo_rootx()+self.app.winfo_width())
                if OUTPUT and size=='1040x760':
                    self.app.attributes('-topmost',True);self.app.lift();self.app.update();time.sleep(.2)
                    x,y=self.app.winfo_rootx(),self.app.winfo_rooty();w,h=self.app.winfo_width(),self.app.winfo_height()
                    ImageGrab.grab(bbox=(x,y,x+w,y+h)).save(OUTPUT/(page.lower().replace(' ','-')+'.png'))
        self.app.nav['News'].focus_force();self.app.update()
        self.app.nav['News'].event_generate('<KeyPress-space>');self.app.nav['News'].event_generate('<KeyRelease-space>')
        time.sleep(.2);self.app.update()
        self.assertEqual(self.app.page_name,'News')
        self.app.news_text.focus_force();self.app.news_text.event_generate('<Tab>');self.app.update()
        self.assertNotEqual(self.app.focus_get(),self.app.news_text)
    def test_refresh_success_offline_error_and_cache(self):
        self.app.rom.set(str(self.rom))
        with patch.object(u,'launcher_feed',return_value=self.feed()):self.app.check();self.wait()
        self.assertEqual(self.app.available.get(),'Release 0.3.6');self.assertEqual(self.app.update_button['state'],'normal')
        self.assertEqual(self.app.news_text['state'],'disabled');self.assertIn('Real release notes.',self.app.news_text.get('1.0','end'))
        self.assertTrue((self.home/'.updates/news-cache.json').is_file())
        with patch.object(u,'launcher_feed',side_effect=OSError('Offline test')):self.app.check();self.wait()
        self.assertIn('saved',self.app.news_status.get());self.assertEqual(self.app.play['state'],'normal')
        self.assertEqual(self.app.news[0]['version'],'0.3.6')
        self.app.news=[];self.app._render_news();self.assertEqual(self.app.news_link['state'],'disabled')
        self.assertIn('Refresh news',self.app.news_text.get('1.0','end'))
    def test_duplicate_launch_running_game_and_guides(self):
        self.app.rom.set(str(self.rom));proc=MagicMock();proc.poll.return_value=None
        with patch('launcher_ui.app.subprocess.Popen',return_value=proc) as spawn, patch('launcher_ui.preferences.running',return_value=False):
            self.app.launch();self.app.launch();self.assertEqual(spawn.call_count,1)
            self.assertEqual(spawn.call_args.args[0][1],str(self.rom.resolve()))
            self.app.release=self.feed()['release'];self.app._sync();self.assertEqual(self.app.update_button['state'],'normal')
        doc=self.home/'docs/PLAYER_GUIDE.md';doc.parent.mkdir();doc.write_text('fixture guide')
        with patch('launcher_ui.app.os.startfile') as open_doc:self.app.guide();open_doc.assert_called_once_with(str(doc))
        with patch('launcher_ui.app.webbrowser.open') as open_web:self.app.guide('KNOWN_ISSUES.md');self.assertIn(u.REPO,open_web.call_args.args[0])

    def test_update_can_stage_while_same_install_game_runs_and_play_recovers(self):
        self.app.rom.set(str(self.rom));self.app.release=self.feed()['release']
        emulator=self.app.root/'builds/current/melonDS.exe';paths=[emulator]
        with patch('launcher_ui.preferences._emulator_paths',side_effect=lambda:paths):
            self.app._process_check_at=0;self.app._sync()
            self.assertEqual(self.app.play['state'],'disabled')
            self.assertEqual(self.app.update_button['state'],'normal')
            with patch.object(u,'install',return_value=self.home):
                self.app.install_update();self.wait()
            self.assertTrue(self.app.status.get().startswith('Update installed.'))
            paths.clear();self.app._process_check_at=0;self.app._sync()
            self.assertEqual(self.app.play['state'],'normal')
    def test_restart_uses_updated_launcher_and_same_home(self):
        launcher=self.app.root/'launcher/Pokemon Together.exe'
        launcher.parent.mkdir(exist_ok=True);launcher.write_bytes(b'fixture launcher')
        from launcher_ui import versioning
        (launcher.parent/'BUILD_INFO.json').write_text(json.dumps({'schema':1,'product':versioning.PRODUCT,'version':versioning.current_version()}))
        with patch('launcher_ui.app.subprocess.Popen') as spawn,patch.object(self.app,'destroy') as close:
            self.app._restart_updated_launcher()
            self.assertEqual(spawn.call_args.args[0],[str(launcher),'--home',str(self.home)])
            self.assertEqual(spawn.call_args.kwargs['cwd'],self.app.root)
            self.assertEqual(spawn.call_args.kwargs['env']['PYINSTALLER_RESET_ENVIRONMENT'],'1')
            close.assert_called_once()
    def test_restart_failure_keeps_launcher_open(self):
        launcher=self.app.root/'launcher/Pokemon Together.exe'
        launcher.parent.mkdir(exist_ok=True);launcher.write_bytes(b'fixture launcher')
        from launcher_ui import versioning
        (launcher.parent/'BUILD_INFO.json').write_text(json.dumps({'schema':1,'product':versioning.PRODUCT,'version':versioning.current_version()}))
        with patch('launcher_ui.app.subprocess.Popen',side_effect=OSError('fixture failure')),patch.object(self.app,'destroy') as close:
            self.app._restart_updated_launcher()
            close.assert_not_called()
            self.assertIn('Could not restart',self.app.status.get())
            self.assertIn('fixture failure',self.app.update_status.get())

    def test_frozen_hub_restart_keeps_shared_launcher_after_mod_update(self):
        hub=self.home/'Pokemon Together.exe';hub.write_bytes(b'hub fixture')
        with patch('launcher_ui.app.sys.frozen',True,create=True),patch('launcher_ui.app.sys.executable',str(hub)),patch('launcher_ui.app.subprocess.Popen') as spawn,patch.object(self.app,'destroy'):
            self.app._restart_updated_launcher()
            self.assertEqual(spawn.call_args.args[0],[str(hub),'--home',str(self.home)])
    def test_real_installation_ui_success(self):
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z:
            z.writestr('Unova-Together/builds/current/melonDS.exe',b'fixture new executable')
            z.writestr('Unova-Together/builds/current/VERSION.txt','0.3.6')
        data=raw.getvalue();feed=self.feed();release=feed['release'];release['size']=len(data)
        sums=(hashlib.sha256(data).hexdigest()+'  '+release['name']+'\n').encode()
        original=u.install
        def install(home,rel,cancel,progress):
            return original(home,rel,cancel,progress,lambda url:io.BytesIO(sums if url==rel['sums'] else data))
        self.app.rom.set(str(self.rom));self.app._save();self.rom.with_suffix('.sav').write_bytes(b'fixture saved game')
        self.app.messages.put(('feed',feed));self.app._poll()
        with patch.object(u,'install',side_effect=install):self.app.install_update();self.wait()
        self.assertTrue(list((self.home/'save-backups').rglob('*.zip')))
        self.assertTrue(self.app.installed.get().startswith('Release 0.3.6'));self.assertEqual(self.app.phase.get()[:5],'Ready')
        self.assertEqual((self.app.root/'builds/current/melonDS.toml').read_text(),'# private controls\n')
        self.assertEqual((self.home/'builds/current/melonDS.exe').read_bytes(),b'not a real executable')
    def test_cancel_failure_and_busy_navigation(self):
        self.app.release=self.feed()['release']
        def slow(home,rel,cancel,progress):
            progress(25,100)
            if cancel.wait(2):raise InterruptedError('Update cancelled')
            raise OSError('Fixture timed out')
        with patch.object(u,'install',side_effect=slow):
            self.app.install_update();self.app.show_page('News');self.app.update_idletasks()
            self.assertEqual(self.app.page_name,'News');self.assertEqual(self.app.check_button['state'],'disabled')
            self.app.cancel_download();self.wait()
        self.assertEqual(u.active_root(self.home),self.home);self.assertIn('cancelled',self.app.update_status.get())
    def test_settings_compatibility_and_persistence(self):
        self.app.show_page('Settings');self.app.rom.set(str(self.rom));self.app._identify_rom()
        self.assertTrue(all('disabled' in c.state() for c in self.app.cheat_buttons.values()))
        profile={'key':'test-rom','digest':'reviewed','profile':'Fixture Black 2'}
        with patch('launcher_ui.preferences.identify',return_value=profile):
            self.app._identify_rom();self.assertTrue(all('disabled' not in c.state() for c in self.app.cheat_buttons.values()))
            self.app.cheat_buttons['repel'].invoke();self.app._preference('volume',35)
        data=json.loads(self.app.config_path.read_text())
        self.assertTrue(data['cheats']['test-rom']['repel']);self.assertEqual(data['preferences']['volume'],35)
        self.app.destroy();self.app=Launcher(self.home,testing=True);self.app.update()
        self.assertEqual(self.app.volume.get(),35)
        with patch('launcher_ui.preferences.identify',return_value=profile):self.app._identify_rom()
        self.assertTrue(self.app.cheat_vars['repel'].get())
        if OUTPUT:
            self.app.geometry('1040x900');self.app.show_page('Settings');self.app.attributes('-topmost',True);self.app.lift();self.app.update();time.sleep(.3);self.app.update()
            box=(self.app.winfo_rootx(),self.app.winfo_rooty(),self.app.winfo_rootx()+self.app.winfo_width(),self.app.winfo_rooty()+self.app.winfo_height())
            ImageGrab.grab(bbox=box).save(OUTPUT/'settings.png')

    def test_settings_save_preserves_preexisting_pending_hardlink(self):
        outside=self.home/'keep-this-file.bin';outside.write_bytes(b'outside data')
        pending=self.app.config_path.with_suffix('.pending');pending.hardlink_to(outside)

        self.app._save()

        self.assertEqual(outside.read_bytes(),b'outside data');self.assertTrue(pending.exists())
        self.assertTrue(json.loads(self.app.config_path.read_text()))

    def test_profiles_and_connection_save_launch_environment(self):
        self.app.rom.set(str(self.rom));self.app.player.set('Tester');self.app._save_profile()
        first=self.app.active_profile_id;self.app._preference('volume',25)
        self.app._new_profile();second=self.app.active_profile_id;self.assertNotEqual(first,second)
        self.app.rom.set(str(self.rom));self.app.player.set('Second');self.app._save_profile();self.app._preference('volume',75)
        self.app.profile_picker.current(0);self.app._select_profile();self.assertEqual(self.app.volume.get(),25);self.assertEqual(self.app.player.get(),'Tester')
        self.app.net_host.set('localhost');self.app.net_room.set('friends');self.app.net_port.set('8765');self.app._save_connection()
        proc=MagicMock();proc.poll.return_value=None
        with patch('launcher_ui.preferences.running',return_value=False),patch('launcher_ui.app.subprocess.Popen',return_value=proc) as spawn:
            self.app.launch();self.assertEqual(spawn.call_args.kwargs['env']['UNOVA_PLAYER_NAME'],'Tester')
            self.assertEqual(spawn.call_args.kwargs['env']['UNOVA_RELAY_ROOM'],'friends')
            self.assertEqual(spawn.call_args.kwargs['env']['UNOVA_COMPANION_INTERACTIONS'],'1')
            self.assertEqual(spawn.call_args.kwargs['env']['UNOVA_EXPERIMENTAL_COMPANION'],'1')

    def test_game_exit_stops_scenery_workers(self):
        proc=MagicMock();proc.poll.return_value=0;self.app.game=proc
        worker=MagicMock();self.app.surroundings_worker=worker
        self.app._reap_game_workers()
        worker.stop.set.assert_called_once_with();worker.thread.join.assert_called_once_with(timeout=.5)
        self.assertIsNone(self.app.surroundings_worker)

    def test_companion_default_and_explicit_off_survive_profile_switch_restart_and_launch(self):
        self.assertTrue(self.app.companion_interactions.get())
        self.assertFalse(self.app.reduced_follower_motion.get())
        self.app._preference('reduced_follower_motion',True)
        self.app._preference('companion_interactions',False)
        first=self.app.active_profile_id
        self.app._new_profile();self.assertTrue(self.app.companion_interactions.get())
        self.app.profile_picker.current(0);self.app._select_profile()
        self.assertEqual(self.app.active_profile_id,first);self.assertFalse(self.app.companion_interactions.get())
        self.app.destroy();self.app=Launcher(self.home,testing=True);self.app._open_mod('black2',save=False);self.app.update()
        self.assertFalse(self.app.companion_interactions.get())
        self.assertTrue(self.app.reduced_follower_motion.get())
        self.app.rom.set(str(self.rom));self.app.player.set('Tester')
        proc=MagicMock();proc.poll.return_value=None
        with patch('launcher_ui.preferences.running',return_value=False),patch('launcher_ui.app.subprocess.Popen',return_value=proc) as spawn:
            self.app.launch()
            self.assertEqual(spawn.call_args.kwargs['env']['UNOVA_COMPANION_INTERACTIONS'],'0')
            self.assertEqual(spawn.call_args.kwargs['env']['UNOVA_EXPERIMENTAL_COMPANION'],'0')
            self.assertEqual(spawn.call_args.kwargs['env']['UNOVA_FOLLOWER_REDUCED_MOTION'],'1')
        self.app.game=None

    def test_connection_worker_and_restore_running_guard(self):
        with patch('launcher_ui.services.probe',return_value='Relay reachable'):
            self.app._check_connection();self.wait();self.assertEqual(self.app.connection_status.get(),'Relay reachable')
        with patch('launcher_ui.preferences.any_running',return_value=True):self.app._restore_backup()
        self.assertIn('Close all melonDS',self.app.status.get())

    def test_check_relay_button_starts_real_local_server(self):
        import socket
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        self.app.net_host.set('127.0.0.1');self.app.net_port.set(str(port))
        try:
            self.app._check_connection();self.wait(12)
            self.assertIn('Local relay started',self.app.connection_status.get())
            self.assertIn('reachable',self.app.connection_status.get())
        finally:
            if self.app.presence_process is not None:
                self.app.presence_process.terminate();self.app.presence_process.wait(timeout=5)

    def test_player_connection_flow_and_advanced_controls(self):
        self.app.net_mode.set('Tailscale backup');self.assertIn('Tailscale',self.app.mode_help.get())
        with patch.object(self.app,'guide') as guide:
            self.app._connection_guide();guide.assert_called_once_with('TAILSCALE_COOP.md')
        self.app.connection_role.set('Join');self.app._connection_role_changed();self.assertEqual(self.app.net_host.get(),'')
        self.app.connection_role.set('Host');self.app._connection_role_changed();self.assertEqual(self.app.net_host.get(),'127.0.0.1')
        self.assertFalse(self.app.advanced_visible)
        self.app._toggle_connection_advanced();self.assertTrue(self.app.advanced_visible)
        self.app._toggle_connection_advanced();self.assertFalse(self.app.advanced_visible)
        self.app.show_page('Co-op');self.app.update();self.app.pages['Co-op'].canvas.yview_moveto(1)
        self.app.show_page('Settings');self.app.show_page('Co-op');self.app.update()
        self.assertLess(self.app.pages['Co-op'].canvas.yview()[0],.01)

    def test_optional_music_preference_and_stop_on_close(self):
        self.assertFalse(self.app.music.get())
        self.app._toggle_music();self.assertTrue(self.app.music.get())
        self.assertTrue(json.loads(self.app.config_path.read_text())['music'])
        self.assertEqual(self.app.music_button['text'],'Music: on')
        self.app._toggle_music();self.assertFalse(self.app.music.get())
        import winsound
        self.app.testing=False
        try:
            with patch.object(winsound,'PlaySound') as sound:
                self.app._toggle_music()
                self.assertTrue(str(sound.call_args.args[0]).endswith('menu-music.wav'))
                self.assertTrue(sound.call_args.args[1]&winsound.SND_LOOP)
                self.app._stop_music();sound.assert_called_with(None,0)
        finally:self.app.testing=True

    def test_lan_launch_handoff_and_status_identity(self):
        self.app.rom.set(str(self.rom));self.app.player.set('Tester');self.app.net_mode.set('Local LAN');self.app._save_profile()
        proc=MagicMock();proc.poll.return_value=None
        with patch('launcher_ui.preferences.running',return_value=False),patch('launcher_ui.app.subprocess.Popen',return_value=proc) as spawn:
            self.app.launch('host')
            env=spawn.call_args.kwargs['env'];self.assertEqual(env['UNOVA_LAN_ACTION'],'host')
            self.assertEqual(len(env['UNOVA_LAN_REQUEST']),32)
            self.assertEqual(env['UNOVA_LAN_SLOTS'],'16')
        report=self.app.root/'builds/current/launcher-lan-status.json'
        report.write_text(json.dumps({'request':'0'*32,'ok':True,'role':1,'players':[]}))
        self.app.lan_status_time=0;self.app._read_lan_status();self.assertIn('Starting LAN',self.app.lan_status.get())
        report.write_text(json.dumps({'request':self.app.lan_request,'ok':True,'role':1,'players':[{'status':1},{'status':2}]}))
        self.app.lan_status_time=0;self.app._read_lan_status();self.assertIn('2 players',self.app.lan_status.get())
        report.write_text(json.dumps({'request':self.app.lan_request,'ok':True,'role':1,'players':[{'status':1}]}))
        self.app.lan_status_time=0;self.app._read_lan_status();self.assertIn('teammate left',self.app.lan_status.get())
        self.app.game=None

    def test_host_button_checks_sharing_before_native_launch(self):
        self.app.rom.set(str(self.rom));self.app.player.set('Tester');self.app.net_host.set('192.0.2.5');self.app.net_mode.set('Local LAN')
        proc=MagicMock();proc.poll.return_value=None
        with patch('launcher_ui.services.check_relay',return_value='Presence relay reachable') as probe,patch('launcher_ui.preferences.running',return_value=False),patch('launcher_ui.app.subprocess.Popen',return_value=proc) as spawn:
            self.app._start_lan('host');self.wait()
            self.assertEqual(probe.call_args.args[0]['host'],'127.0.0.1')
            self.assertEqual(spawn.call_args.kwargs['env']['UNOVA_LAN_ACTION'],'host')
        self.app.game=None

    def test_remember_join_address_and_guard_retry(self):
        self.app.connection_role.set('Join');self.app.net_host.set('192.0.2.10');self.app._save_connection()
        self.app.connection_role.set('Host');self.app._connection_role_changed()
        self.app.connection_role.set('Join');self.app._connection_role_changed()
        self.assertEqual(self.app.net_host.get(),'192.0.2.10')
        stored=json.loads(self.app.config_path.read_text())['profiles'][0]
        self.assertEqual(stored['lan_role'],'Join');self.assertEqual(stored['join_host'],'192.0.2.10')
        proc=MagicMock();proc.poll.return_value=None;self.app.game=proc
        with patch.object(self.app,'_start_lan') as start:
            self.app._retry_lan();start.assert_not_called()
        self.assertIn('Save and close',self.app.lan_status.get());self.app.game=None
        with patch.object(self.app,'_start_lan') as start:
            self.app._retry_lan();start.assert_called_once_with('join')

    def test_controller_navigation_and_diagnostic_review(self):
        self.app._cycle_page(1);self.assertEqual(self.app.page_name,'Co-op')
        self.app._controller_action('back');self.assertEqual(self.app.page_name,'Play')
        self.app.nav['Features'].focus_force();self.app.update();self.app._controller_action('accept')
        self.assertEqual(self.app.page_name,'Features')
        from launcher_ui.controller import Pad,actions,Controller
        pad=Pad();pad.buttons=0x1001;self.assertEqual(actions(pad),{'up','accept'})
        controller=Controller();controller.api=None;self.assertFalse(controller.poll(True));self.assertFalse(controller.poll(False))
        report=self.home/'review.zip'
        from launcher_ui import services
        services.diagnostics(self.home,report)
        self.app._review_report(report);self.app.update()
        windows=[w for w in self.app.winfo_children() if w.winfo_class()=='Toplevel']
        self.assertTrue(windows)
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        folder_button=next(child for child in descendants(windows[0])
                           if 'text' in child.keys() and child.cget('text')=='Open report folder')
        callback_errors=[]
        self.app.report_callback_exception=lambda kind,value,traceback:callback_errors.append(value)
        with patch('launcher_ui.app.os.startfile',side_effect=PermissionError('folder unavailable')):
            folder_button.invoke()
        self.assertFalse(callback_errors)
        self.assertIn('Could not open report folder',self.app.status.get())
        self.assertIn('folder unavailable',self.app.status.get())
        for window in windows:window.destroy()

    def test_theme_contract_drift(self):
        import re
        document=json.loads((HERE/'theme.json').read_text(encoding='utf-8'))
        self.assertEqual(set(document),{'colors','fonts','layout'})
        self.assertEqual(document,THEME)
        self.assertTrue(document['colors'])
        self.assertTrue(all(re.fullmatch(r'#[0-9a-fA-F]{6}',value) for value in document['colors'].values()))
        self.assertTrue(all(isinstance(value,str) and value for value in document['fonts'].values()))
        self.assertTrue(all(isinstance(value,int) and value>0 for value in document['layout'].values()))

    def test_all_settings_editor_and_saved_relay(self):
        from launcher_ui.settings_editor import SettingsEditor
        editor=SettingsEditor(self.app,self.home/'builds/current');editor.update_idletasks()
        if OUTPUT:
            editor.lift();editor.focus_force();editor.update();time.sleep(.3);editor.update();x,y=editor.winfo_rootx(),editor.winfo_rooty()
            ImageGrab.grab(bbox=(x,y,x+editor.winfo_width(),y+editor.winfo_height())).save(OUTPUT/'all-emulator-settings.png')
        self.assertGreater(len(editor.tree.get_children()),170)
        editor.search.set('Keyboard.A');self.assertTrue(editor.tree.get_children())
        editor.tree.selection_set('Instance0.Keyboard.A');editor.select();editor.value.set('90');editor.stage()
        with patch('launcher_ui.preferences.running',return_value=False):editor.commit()
        self.assertIn('Settings saved',editor.status.get());editor.destroy()
        self.app.net_host.set('127.0.0.2');self.app.net_port.set('9876');self.app.net_room.set('changed')
        self.app._save_connection()
        saved=json.loads((self.home/'builds/current/launcher-connection.json').read_text())
        self.assertEqual(saved['host'],'127.0.0.2');self.assertEqual(saved['room'],'changed')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args,rest=parser.parse_known_args()
    OUTPUT=args.output
    if OUTPUT:OUTPUT.mkdir(parents=True,exist_ok=False)
    unittest.main(argv=['test_launcher_ui.py',*rest])

