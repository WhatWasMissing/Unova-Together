"""Native launcher UI by mvq1303 / WhatWasMissing. Updater owns installation."""
from pathlib import Path
import json, os, queue, re, time, uuid, subprocess, sys, threading, tkinter as tk, webbrowser, zipfile
import tomlkit
from tkinter import filedialog, messagebox, ttk
import unova_updater as updates
import unova_storage as storage
import launcher_migration
from . import preferences as prefs
from . import services
from . import gen5_tools
from . import player_models
from . import cynthia_event
from . import game_routes
from . import versioning
from .components import C, F, HERE, THEME, ScrollPage, button, card, emblem, label, set_enabled

class Launcher(tk.Tk):
    def __init__(self,home,testing=False):
        super().__init__()
        self.home=Path(home).resolve();self.root=updates.active_root(self.home,allow_missing=True);self.testing=testing
        self.config_path=self.home/'.launcher-test.json' if testing else Path(os.environ.get('APPDATA',Path.home()))/'UnovaTogether/launcher.json'
        self.title('Pokemon Together');self.geometry('1040x760');self.minsize(860,660);self.configure(bg=C['background'])
        try:self.iconbitmap(str(HERE/'assets/launcher.ico'))
        except tk.TclError:pass
        self.messages=queue.Queue();self.busy=False;self.release=None;self.game=None;self.operation='';self.guides_busy=False
        self._process_check_at=0;self._process_running=False
        self.cancel=threading.Event();self.rom=tk.StringVar();self.auto=tk.BooleanVar(value=True);self.music=tk.BooleanVar(value=False)
        self.status=tk.StringVar(value='');self.news_status=tk.StringVar(value='Saved patch notes · available offline')
        self.update_status=tk.StringVar(value='Check GitHub for the latest Windows release.')
        self.available=tk.StringVar(value='Not checked yet');self.phase=tk.StringVar(value='No download in progress')
        self.news=self._read_news();self.pages={};self.nav={};self.images=[];self.page_name=''
        self.feature_mega_frames=[];self.feature_mega_labels=[];self.feature_mega_frame=0;self.feature_mega_after=None
        self.preference_values={};self.cheat_choices={};self.profile=None;self.rom_timer=None
        self.play_profiles=[];self.active_profile_id='';self.repair_release=None;self._switching=False
        self.presence_process=None;self.lan_request='';self.lan_status_time=0;self.lan_started=0;self.last_lan_action='host';self.lan_was_connected=False
        self.selected_game=tk.StringVar(value=game_routes.GAMES['black2']);self.research_root=tk.StringVar(value=str(self.home/'3ds-coop') if (self.home/'3ds-coop/tools/start_joinable_session.ps1').is_file() else 'F:/pokemon-x-coop' if Path('F:/pokemon-x-coop/tools/start_joinable_session.ps1').is_file() else '');self.research_mode=tk.StringVar(value='Local two players');self.research_address=tk.StringVar(value='127.0.0.1')
        self.active_mod=None;self.unova_started=False;self.library_buttons={}
        self._read_settings();self._init_profiles();self._build();self._apply_navigation();self.show_page('Library');self._rom_changed()
        self.rom.trace_add('write',lambda *_:self._rom_changed());self.protocol('WM_DELETE_WINDOW',self._close)
        self.bind('<Control-Tab>',lambda e:self._cycle_page(1));self.bind('<Control-Shift-Tab>',lambda e:self._cycle_page(-1))
        self.bind_class('Button','<Return>',lambda e:e.widget.invoke())
        from .controller import Controller
        self.controller=Controller();self.after(125,self._poll_controller)
        self.bind('<MouseWheel>',self._wheel);self.after(100,self._poll);self._sync();self._music_changed(save=False)

    def _build(self):
        style=ttk.Style(self);style.theme_use('clam')
        style.configure('TScrollbar',background=C['border'],troughcolor=C['background'],arrowcolor=C['muted'],borderwidth=0)
        style.configure('TProgressbar',background=C['primary'],troughcolor=C['selection'],borderwidth=0)
        style.configure('TCheckbutton',background=C['background'],foreground=C['text'],font=(F['body'],11))
        style.map('TCheckbutton',background=[('active',C['selection'])])
        self.nav_cursor=tk.PhotoImage(file=HERE/'assets/menu-cursor.png');self.images.append(self.nav_cursor)
        sidebar=tk.Frame(self,bg=C['nav'],width=THEME['layout']['sidebar']);sidebar.pack(side='left',fill='y');sidebar.pack_propagate(False)
        emblem(sidebar,size=48).pack(anchor='w',padx=23,pady=(16,8))
        label(sidebar,'POKEMON\nTOGETHER',size=18,bold=True,color=C['surface'],bg=C['nav'],role='display',justify='left').pack(anchor='w',padx=24)
        self.mod_caption=label(sidebar,'MULTIPLAYER MODS',size=9,color=C['navText'],bg=C['nav'],wraplength=150)
        self.mod_caption.pack(anchor='w',padx=24,pady=(12,8))
        for name in ('Library','Play','Co-op','Features','Profiles','News','Updates','Settings','Tools','Setup','XPlay','XCoop','XGuides'):
            self.nav[name]=button(sidebar,game_routes.PAGE_LABELS.get(name,name),lambda n=name:self.show_page(n),kind='nav',anchor='w')
            self.nav[name].pack(fill='x',padx=12,pady=3)
        credit=tk.Frame(sidebar,bg=C['nav']);credit.pack(side='bottom',fill='x',padx=24,pady=16)
        label(credit,'Made by mvq1303',size=10,color=C['surface'],bg=C['nav']).pack(anchor='w')
        label(credit,'WhatWasMissing\nBuilt on melonDS / Azahar',size=9,color=C['navText'],bg=C['nav'],justify='left').pack(anchor='w',pady=(5,0))
        shell=tk.Frame(self,bg=C['background']);shell.pack(side='right',fill='both',expand=True)
        footer=tk.Frame(shell,bg=C['surface'],height=48,highlightbackground=C['border'],highlightthickness=1);footer.pack(side='bottom',fill='x');footer.pack_propagate(False)
        self.music_button=button(footer,'Music: off',self._toggle_music);self.music_button.pack(side='right',padx=4)
        self.footer_version=label(footer,self._version_text(),size=9,color=C['muted'],bg=C['surface'],role='utility');self.footer_version.pack(side='right',padx=18)
        self.footer_status=label(footer,size=9,bg=C['surface'],textvariable=self.status);self.footer_status.pack(side='left',fill='x',expand=True,padx=18)
        credits_bar=tk.Frame(shell,bg=C['surface'],highlightbackground=C['border'],highlightthickness=1)
        credits_bar.pack(side='bottom',fill='x')
        self.playtester_credit=label(credits_bar,'Playtesters: maxback221 · randomitem19',size=10,color=C['nav'],bg=C['surface'],justify='left')
        self.playtester_credit.pack(fill='x',padx=18,pady=7)
        credits_bar.bind('<Configure>',lambda e:self.playtester_credit.configure(wraplength=max(100,e.width-36)),add='+')
        self.deck=tk.Frame(shell,bg=C['background']);self.deck.pack(fill='both',expand=True,padx=THEME['layout']['padding'],pady=THEME['layout']['padding'])
        for name in ('Library','Play','Profiles','Co-op','Features','Updates','Settings','Tools','Setup','XPlay','XCoop','XGuides'):self.pages[name]=ScrollPage(self.deck)
        self.pages['News']=tk.Frame(self.deck,bg=C['background'])
        self._features_page(self.pages['Features'].content);self._play_page(self.pages['Play'].content);self._updates_page(self.pages['Updates'].content)
        self._news_page(self.pages['News']);self._settings_page(self.pages['Settings'].content);self._profiles_page(self.pages['Profiles'].content);self._coop_page(self.pages['Co-op'].content);self._tools_page(self.pages['Tools'].content);self._setup_page(self.pages['Setup'].content)
        self._library_page(self.pages['Library'].content)
        self._research_play_page(self.pages['XPlay'].content)
        self._research_coop_page(self.pages['XCoop'].content)
        self._research_guides_page(self.pages['XGuides'].content)
        self.deck.bind('<Configure>',lambda e:self.footer_status.configure(wraplength=max(220,e.width-175)))

    def _heading(self,parent,kicker,title,subtitle):
        label(parent,title,size=25,bold=True,role='display').pack(anchor='w',pady=(0,0 if subtitle else 16))
        note=label(parent,subtitle,size=10,color=C['muted'],wraplength=700,justify='left');note.pack(anchor='w',pady=(7,16)) if subtitle else None
        parent.bind('<Configure>',lambda e:note.configure(wraplength=max(280,e.width-12)),add='+')

    def _library_page(self,parent):
        self._heading(parent,'LIBRARY','Mod library','')
        self.library_details={}
        for mod,spec in game_routes.MODS.items():
            row=card(parent);row.pack(fill='x',pady=(0,16))
            heading=tk.Frame(row,bg=C['hero']);heading.pack(fill='x')
            label(heading,spec['platform'].upper(),size=9,color=C['accent'],bg=C['hero'],role='utility').pack(anchor='w',padx=20,pady=(14,4))
            label(heading,spec['name'],size=21,bold=True,color=C['surface'],bg=C['hero'],role='display').pack(anchor='w',padx=20,pady=(0,14))
            body=tk.Frame(row,bg=C['surface']);body.pack(fill='x',padx=20,pady=16)
            copy=label(body,spec['description'],size=11,bg=C['surface'],wraplength=580,justify='left');copy.pack(anchor='w')
            body.bind('<Configure>',lambda e,w=copy:w.configure(wraplength=max(240,e.width)))
            self.library_details[mod]=tk.StringVar(value=self._version_text() if mod=='black2' else spec['status'])
            label(body,textvariable=self.library_details[mod],size=9,color=C['muted'],bg=C['surface']).pack(anchor='w',pady=(8,12))
            self.library_buttons[mod]=button(body,'Open '+spec['name'],lambda key=mod:self._open_mod(key),kind='primary')
            self.library_buttons[mod].pack(anchor='w')

    def _research_play_page(self,parent):
        self._heading(parent,'POKEMON X','Pokemon X Together','')
        self.research_card=card(parent);self.research_card.pack(fill='x')
        note=label(self.research_card,'Experimental prototype. Switching, fainting replacement and guest rewards are unfinished. Do not save trial progress.',size=10,bg=C['surface'],color=C['warning'],wraplength=600,justify='left')
        note.pack(anchor='w',padx=18,pady=(18,14))
        self.research_card.bind('<Configure>',lambda e:note.configure(wraplength=max(260,e.width-40)))
        label(self.research_card,'Pokemon X mod folder',size=10,bg=C['surface']).pack(anchor='w',padx=18)
        folder=tk.Frame(self.research_card,bg=C['surface']);folder.pack(fill='x',padx=18,pady=(4,12))
        self.research_folder_entry=tk.Entry(folder,textvariable=self.research_root,font=(F['body'],11),highlightthickness=2,highlightcolor=C['focus'])
        self.research_folder_entry.pack(side='left',fill='x',expand=True)
        button(folder,'Browse',self._browse_research).pack(side='left',padx=(8,0))
        label(self.research_card,'Launch mode',size=10,bg=C['surface']).pack(anchor='w',padx=18)
        ttk.Combobox(self.research_card,textvariable=self.research_mode,values=list(game_routes.MODES),state='readonly',font=(F['body'],11)).pack(fill='x',padx=18,pady=(4,12))
        label(self.research_card,'Host IPv4 address (joining over LAN)',size=10,bg=C['surface']).pack(anchor='w',padx=18)
        tk.Entry(self.research_card,textvariable=self.research_address,font=(F['body'],11),highlightthickness=2,highlightcolor=C['focus']).pack(fill='x',padx=18,pady=(4,12))
        self.research_play=button(self.research_card,'Open Pokemon X co-op',self._launch_research,kind='primary')
        self.research_play.pack(anchor='w',padx=18,pady=(0,18))
        button(parent,'Connection and controls',lambda:self.show_page('XCoop')).pack(anchor='w',pady=14)

    def _research_coop_page(self,parent):
        self._heading(parent,'CO-OP','Co-op','')
        self.research_launch_buttons=[]
        for title,copy,mode in (
            ('Two players on this PC','Opens two independent games and the local multiplayer service.','local'),
            ('Host a LAN room','Your teammate needs the prepared mod and your room credential file.','host'),
            ('Join a LAN room','Set your friend\'s IPv4 address on Play and copy their room credential into your mod folder.','guest')):
            row=card(parent);row.pack(fill='x',pady=(0,12))
            label(row,title,size=13,bold=True,bg=C['surface']).pack(anchor='w',padx=18,pady=(16,6))
            note=label(row,copy,size=10,color=C['muted'],bg=C['surface'],wraplength=560,justify='left');note.pack(anchor='w',padx=18,pady=(0,10))
            row.bind('<Configure>',lambda e,w=note:w.configure(wraplength=max(240,e.width-40)))
            action=button(row,'Start two players' if mode=='local' else 'Host room' if mode=='host' else 'Join room',lambda role=mode:self._launch_research(role),kind='primary')
            action.pack(anchor='w',padx=18,pady=(0,16));self.research_launch_buttons.append(action)
        label(parent,'Close previous Pokemon X game windows before starting. F8 invites your teammate; they choose Join battle. F9 on both players enables automatic trainer participation.',size=10,wraplength=590,justify='left').pack(anchor='w',pady=8)
        button(parent,'LAN guide',lambda:self._research_guide('LAN_AND_ANIMATION_ALPHA.md')).pack(anchor='w',pady=8)

    def _research_guides_page(self,parent):
        self._heading(parent,'GUIDES','Guides','')
        for title,doc in (('Trainer co-op and controls','TRAINER_COOP_ALPHA.md'),('LAN setup and player visibility','LAN_AND_ANIMATION_ALPHA.md'),('Native battle menus','NATIVE_SIMULTANEOUS_MENUS.md'),('Connection recovery','SESSION_RESILIENCE.md')):
            button(parent,title,lambda name=doc:self._research_guide(name)).pack(fill='x',pady=(0,12))

    def _research_guide(self,name):
        path=Path(self.research_root.get())/name
        try:
            if not path.is_file():raise OSError('Guide missing. Choose the prepared Pokemon X folder on Play.')
            os.startfile(str(path))
        except OSError as exc:self.status.set(str(exc))

    def _play_page(self,parent):
        self._heading(parent,'PLAY','Play','')
        hero=tk.Frame(parent,bg=C['hero'],height=THEME['layout']['heroHeight']);hero.pack(fill='x');hero.pack_propagate(False)
        try:
            picture=tk.PhotoImage(file=HERE/'assets/explore.png');self.images.append(picture)
        except tk.TclError:picture=None
        art=tk.Label(hero,image=picture,bg=C['hero'],bd=0);art.pack(side='right',padx=(0,18),pady=18)
        words=tk.Frame(hero,bg=C['hero']);words.pack(side='left',fill='both',expand=True,padx=24,pady=24)
        label(words,'BLAZE BLACK 2 REDUX · CO-OP',size=9,bold=True,color=C['accent'],bg=C['hero']).pack(anchor='w')
        label(words,'Pokemon\nTogether',size=25,bold=True,color=C['surface'],bg=C['hero'],role='display',justify='left').pack(anchor='w',pady=(10,12))
        starters=tk.Frame(words,bg=C['hero']);starters.pack(anchor='w')
        for species in (495,498,501):
            try:
                sprite=tk.PhotoImage(file=HERE/f'assets/gen5-{species}.png');self.images.append(sprite)
                tk.Label(starters,image=sprite,bg=C['hero'],bd=0).pack(side='left')
            except tk.TclError:pass
        def fit(e):
            if e.width<675:art.pack_forget()
            elif not art.winfo_manager():art.pack(side='right',padx=(0,18),pady=18,before=words)
        hero.bind('<Configure>',fit)
        self.ds_hero=hero
        game=card(parent);self.ds_game_card=game;game.pack(fill='x',pady=(18,15))
        inner=tk.Frame(game,bg=C['surface']);inner.pack(fill='x',padx=18,pady=16);inner.columnconfigure(0,weight=1)
        label(inner,'Game ROM',size=9,bold=True,color=C['muted'],bg=C['surface']).grid(row=0,column=0,sticky='w')
        self.rom_entry=tk.Entry(inner,textvariable=self.rom,font=(F['body'],11),bg=C['background'],fg=C['text'],relief='flat',
            highlightthickness=2,highlightbackground=C['border'],highlightcolor=C['focus'],insertbackground=C['text'])
        self.rom_entry.grid(row=1,column=0,sticky='ew',ipady=10,pady=(8,0))
        button(inner,'Browse',self.browse).grid(row=1,column=1,padx=(8,0),pady=(8,0))
        self.play=button(inner,'Play',self.launch,kind='primary',width=9);self.play.grid(row=1,column=2,padx=(8,0),pady=(8,0))
        self.game_hint=label(inner,size=9,color=C['muted'],bg=C['surface']);self.game_hint.grid(row=2,column=0,columnspan=3,sticky='w',pady=(10,0))
        self.active_slot=tk.StringVar(value='Save slot: '+self._active_profile()['label'])
        label(inner,textvariable=self.active_slot,size=10,bg=C['surface']).grid(row=3,column=0,sticky='w',pady=(10,0))
        button(inner,'Manage saves',lambda:self.show_page('Profiles')).grid(row=3,column=1,columnspan=2,sticky='e',pady=(10,0))

    def _updates_page(self,parent):
        self._heading(parent,'UPDATES','Updates','Use the same version as your friend.')
        self.installed=tk.StringVar(value=self._version_text());versions=card(parent);versions.pack(fill='x')
        for caption,value in (('INSTALLED',self.installed),('ON GITHUB',self.available)):
            block=tk.Frame(versions,bg=C['surface']);block.pack(side='left',fill='both',expand=True,padx=22,pady=22)
            label(block,caption,size=9,bold=True,color=C['muted'],bg=C['surface']).pack(anchor='w')
            label(block,size=19,bold=True,bg=C['surface'],textvariable=value).pack(anchor='w',pady=(9,0))
        status=card(parent);status.pack(fill='x',pady=18);inner=tk.Frame(status,bg=C['surface']);inner.pack(fill='x',padx=22,pady=22)
        label(inner,'OFFICIAL GITHUB UPDATES',size=9,bold=True,color=C['primary'],bg=C['surface']).pack(anchor='w')
        msg=label(inner,textvariable=self.update_status,size=12,bold=True,bg=C['surface'],wraplength=630,justify='left');msg.pack(anchor='w',pady=(10,17))
        inner.bind('<Configure>',lambda e:msg.configure(wraplength=max(250,e.width)))
        self.bar=ttk.Progressbar(inner,maximum=100);self.bar.pack(fill='x',ipady=3)
        label(inner,textvariable=self.phase,size=9,color=C['muted'],bg=C['surface']).pack(anchor='w',pady=(10,15))
        actions=tk.Frame(inner,bg=C['surface']);actions.pack(fill='x')
        self.check_button=button(actions,'Check for updates',self.check);self.check_button.pack(side='left')
        self.update_button=button(actions,'Install update',self.install_update,kind='primary');self.update_button.pack(side='left',padx=10)
        self.cancel_button=button(actions,'Cancel download',self.cancel_download);self.cancel_button.pack(side='left')
        button(parent,'Launcher settings',lambda:self.show_page('Settings')).pack(anchor='w',pady=(0,18))
        safety=card(parent);safety.pack(fill='x');label(safety,'Your saves are kept',size=12,bold=True,bg=C['surface']).pack(anchor='w',padx=20,pady=(18,10))
        label(safety,'Verified downloads. Saves, ROMs and settings are kept.',size=10,color=C['muted'],bg=C['surface'],justify='left').pack(anchor='w',padx=20,pady=(0,20))

    def _news_page(self,parent):
        self._heading(parent,'NEWS','News','')
        tools=tk.Frame(parent,bg=C['background']);tools.pack(fill='x',pady=(0,16))
        label(tools,textvariable=self.news_status,size=9,color=C['muted']).pack(side='left')
        self.refresh_news=button(tools,'Refresh news',self.check);self.refresh_news.pack(side='right')
        panel=card(parent);panel.pack(fill='both',expand=True)
        picker_frame=tk.Frame(panel,bg=C['selection']);picker_frame.pack(fill='x',padx=14,pady=(14,10))
        self.news_picker=tk.Listbox(picker_frame,height=3,font=(F['body'],11),bg=C['selection'],fg=C['text'],selectbackground=C['primary'],selectforeground=C['surface'],
            activestyle='none',exportselection=False,relief='flat',highlightthickness=2,highlightcolor=C['focus'],highlightbackground=C['selection'])
        picker_bar=ttk.Scrollbar(picker_frame,command=self.news_picker.yview);picker_bar.pack(side='right',fill='y')
        self.news_picker.configure(yscrollcommand=picker_bar.set);self.news_picker.pack(fill='x');self.news_picker.bind('<<ListboxSelect>>',self.select_news)
        content=tk.Frame(panel,bg=C['surface']);content.pack(fill='both',expand=True,padx=18)
        self.news_text=tk.Text(content,wrap='word',font=(F['body'],11),bg=C['surface'],fg=C['text'],relief='flat',padx=4,pady=10,spacing1=3,spacing3=8,
            highlightthickness=2,highlightcolor=C['focus'],highlightbackground=C['surface'],cursor='arrow')
        scroll=ttk.Scrollbar(content,command=self.news_text.yview);scroll.pack(side='right',fill='y');self.news_text.configure(yscrollcommand=scroll.set);self.news_text.pack(fill='both',expand=True)
        self.news_text.tag_configure('heading',font=(F['body'],17,'bold'),foreground=C['text'],spacing1=10,spacing3=12)
        self.news_text.tag_configure('subheading',font=(F['body'],12,'bold'),foreground=C['primary'],spacing1=10)
        self.news_text.bind('<Tab>',lambda e:(e.widget.tk_focusNext().focus_set(),'break')[1])
        self.news_text.bind('<Shift-Tab>',lambda e:(e.widget.tk_focusPrev().focus_set(),'break')[1])
        bottom=tk.Frame(panel,bg=C['surface']);bottom.pack(side='bottom',fill='x',padx=18,pady=14,before=content)
        self.news_link=button(bottom,'Read on GitHub',self.open_news);self.news_link.pack(side='left');self._render_news()

    def _setup_page(self,parent):
        self._heading(parent,'SETUP','Setup guides','')
        self.guide_status=tk.StringVar(value='Local guides available offline')
        button(parent,'Refresh guides',self.refresh_guides).pack(anchor='w',pady=(0,6))
        label(parent,textvariable=self.guide_status,size=9,color=C['muted']).pack(anchor='w',pady=(0,12))
        for title,copy,doc in (
            ('First time playing?','Choose your ROM, connect player sharing, then create a native LAN game.','PLAYER_GUIDE.md'),
            ('Playing on different networks','Use the Tailscale guide, or try the experimental UDP bridge.','TAILSCALE_COOP.md'),
            ('Experimental UDP setup','Your group supplies a server. No public server is included.','UDP_SERVER_GUIDE.md'),
            ('Before reporting a problem','Check the known limitations and recovery advice.','KNOWN_ISSUES.md')):
            row=card(parent);row.pack(fill='x',pady=(0,12));button(row,'Open guide',lambda d=doc:self.guide(d)).pack(side='right',padx=16,pady=20)
            text=tk.Frame(row,bg=C['surface']);text.pack(side='left',fill='both',expand=True,padx=18,pady=17)
            label(text,title,size=12,bold=True,bg=C['surface']).pack(anchor='w')
            info=label(text,copy,size=10,color=C['muted'],bg=C['surface'],wraplength=470,justify='left');info.pack(anchor='w',pady=(6,0))
            text.bind('<Configure>',lambda e,w=info:w.configure(wraplength=max(200,e.width)))
        notice=tk.Frame(parent,bg=C['warningSurface']);notice.pack(fill='x',pady=(5,0))
        label(notice,'Turn C-Gear wireless and fast-forward off for co-op.',size=10,bold=True,color=C['warning'],bg=C['warningSurface']).pack(anchor='w',padx=18,pady=16)

    def show_page(self,name):
        if name=='Library' and self.active_mod is not None:self._return_library();return
        if name not in self.visible_pages:return
        if name=='Profiles':self._save();self._refresh_backups()
        for page in self.pages.values():page.pack_forget()
        self.pages[name].pack(fill='both',expand=True);self.page_name=name
        self._set_feature_mega_animation(name=='Features')
        context=game_routes.MODS[self.active_mod]['name']+' · ' if self.active_mod and name!='Library' else ''
        self.title('Pokemon Together · '+context+game_routes.PAGE_LABELS.get(name,name))
        if isinstance(self.pages[name],ScrollPage):self.pages[name].canvas.yview_moveto(0)
        for key,b in self.nav.items():b.configure(bg=C['selection'] if key==name else C['nav'],fg=C['text'] if key==name else C['navText'],highlightbackground=C['selection'] if key==name else C['nav'],image=self.nav_cursor if key==name else '',compound='left')

    def _wheel(self,event):
        page=self.pages.get(self.page_name);widget=event.widget
        if not isinstance(page,ScrollPage):return
        while widget is not None:
            if widget==page:page.wheel(event);return
            widget=getattr(widget,'master',None)

    def _version_text(self):
        try:return 'Release '+'.'.join(map(str,updates.local_version(self.root)))+' · Launcher '+versioning.current_version()
        except (OSError,ValueError):return 'Build unavailable'

    def _read_news(self):
        for path in (self.home/'.updates/news-cache.json',HERE/'assets/news.json'):
            try:
                if path.stat().st_size>512*1024:continue
                raw=json.loads(path.read_text(encoding='utf-8'))
                if isinstance(raw,dict) and raw.get('schema')==1:
                    news=updates.patch_note_news(raw.get('notes'))
                elif isinstance(raw,list):
                    try:news=updates.patch_note_news(raw)
                    except ValueError:
                        news=updates.release_news([{'tag_name':'v'+n['version'],'name':n.get('title'),'body':n.get('body'),'published_at':n.get('date')} for n in raw[:30] if isinstance(n,dict)])
                else:continue
                if news:return news
            except (OSError,ValueError,KeyError,TypeError):continue
        return []

    def _render_news(self):
        self.news_picker.delete(0,'end')
        for n in self.news:self.news_picker.insert('end',n['version']+'  ·  '+n['title'])
        if self.news:self.news_picker.selection_set(0);self.select_news()
        else:
            self.news_text.configure(state='normal');self.news_text.delete('1.0','end');self.news_text.insert('end','No saved patch notes yet. Select Refresh news to load them from GitHub.')
            self.news_text.configure(state='disabled');set_enabled(self.news_link,False)

    def select_news(self,event=None):
        chosen=self.news_picker.curselection()
        if not chosen or chosen[0]>=len(self.news):return
        n=self.news[chosen[0]];self.news_text.configure(state='normal');self.news_text.delete('1.0','end')
        self.news_text.insert('end',n['title']+'\n','heading')
        source=('Published '+n['date']+' · ' if n.get('date') else '')+'Official GitHub patch notes\n\n'
        self.news_text.insert('end',source)
        lines=n['body'].splitlines()
        if lines and lines[0].startswith('# '):lines=lines[1:]
        for line in lines:
            heading=line.startswith('#');line=re.sub(r'^#+\s*','',line);line=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',line).replace('**','').replace('`','')
            self.news_text.insert('end',line+'\n','subheading' if heading else ())
        self.news_text.configure(state='disabled');self.news_text.yview_moveto(0);set_enabled(self.news_link,True)

    def open_news(self):
        chosen=self.news_picker.curselection()
        if chosen and chosen[0]<len(self.news):webbrowser.open(self.news[chosen[0]]['url'])

    def _active_profile(self):
        return next(i for i in self.play_profiles if i['id']==self.active_profile_id)

    def _init_profiles(self):
        if not self.play_profiles:
            item=services.profile(self.rom.get());item['preferences']=dict(self.preference_values)
            try:
                runtime=self.root/'builds/current';value=prefs.read_document(runtime).get('Instance0',{}).get('SaveFilePath','')
                if value:item['save_dir']=str((runtime/value).resolve()) if not Path(value).is_absolute() else value
            except (OSError,ValueError):pass
            self.play_profiles=[item]
        if not any(i['id']==self.active_profile_id for i in self.play_profiles):self.active_profile_id=self.play_profiles[0]['id']
        item=self._active_profile();item.setdefault('preferences',{});item.setdefault('save_dir','');item.setdefault('player','Player');item.setdefault('label','Game')
        item.setdefault('network',services.profile()['network'])
        self.preference_values=dict(item['preferences']);self.rom.set(item['rom'])

    def _field(self,parent,title,variable,row):
        label(parent,title,size=10,bg=C['surface']).grid(row=row,column=0,sticky='w',pady=7,padx=(0,12))
        entry=tk.Entry(parent,textvariable=variable,font=(F['body'],11),bg=C['background'],fg=C['text'],relief='flat',highlightthickness=2,highlightbackground=C['border'],highlightcolor=C['focus'])
        entry.grid(row=row,column=1,sticky='ew',ipady=7,pady=7);return entry

    def _profiles_page(self,parent):
        self._heading(parent,'YOUR GAMES','Games & saves','Choose a save slot. Each slot keeps its own saves, backups and settings.')
        box=card(parent);box.pack(fill='x');inner=tk.Frame(box,bg=C['surface']);inner.pack(fill='x',padx=18,pady=18);inner.columnconfigure(1,weight=1)
        self.profile_picker=ttk.Combobox(inner,state='readonly',values=[i['label'] for i in self.play_profiles]);self.profile_picker.grid(row=0,column=0,columnspan=2,sticky='ew',pady=(0,15));self.profile_picker.current(self.play_profiles.index(self._active_profile()));self.profile_picker.bind('<<ComboboxSelected>>',self._select_profile)
        item=self._active_profile();self.profile_label=tk.StringVar(value=item['label']);self.player=tk.StringVar(value=item['player']);self.save_dir=tk.StringVar(value=item['save_dir'])
        self._field(inner,'Save slot name',self.profile_label,1)
        self.profile_game=tk.StringVar();label(inner,textvariable=self.profile_game,size=10,color=C['muted'],bg=C['surface'],wraplength=550,justify='left').grid(row=2,column=0,columnspan=2,sticky='w',pady=8)
        button(inner,'Choose game ROM',lambda:self.show_page('Play')).grid(row=3,column=0,sticky='w',pady=4)
        button(inner,'New save slot',self._new_profile).grid(row=3,column=1,sticky='e',pady=4)
        self.save_summary=tk.StringVar();label(parent,textvariable=self.save_summary,size=10,color=C['muted'],wraplength=620,justify='left').pack(anchor='w',pady=(16,8))
        self.backup_button=button(parent,'Back up now',self._backup_now,kind='primary');self.backup_button.pack(anchor='w',pady=(0,14))
        label(parent,'Restore a backup',size=12,bold=True).pack(anchor='w')
        self.backup_picker=ttk.Combobox(parent,state='readonly');self.backup_picker.pack(fill='x',pady=(8,10))
        self.restore_button=button(parent,'Restore backup',self._restore_backup);self.restore_button.pack(anchor='w')
        label(parent,'Close the game before restoring. Your current save is backed up first.',size=9,color=C['muted'],wraplength=620,justify='left').pack(anchor='w',pady=(8,12))
        self.profile_advanced=tk.Frame(parent,bg=C['background']);self.profile_advanced.columnconfigure(1,weight=1)
        self.profile_advanced_visible=False;self.profile_advanced_button=button(parent,'Advanced save options',self._toggle_profile_advanced);self.profile_advanced_button.pack(anchor='w',pady=8)
        for title,var,row in [('Player name',self.player,0),('Custom save folder',self.save_dir,1)]:
            self._field(self.profile_advanced,title,var,row)
        button(self.profile_advanced,'Choose folder',self._browse_save_dir).grid(row=2,column=1,sticky='w',pady=8)
        label(self.profile_advanced,'Blank uses the ROM folder. Changing folders does not move existing saves.',size=9,color=C['muted'],wraplength=550,justify='left').grid(row=3,column=0,columnspan=2,sticky='w',pady=8)
        button(self.profile_advanced,'Open backups folder',self._open_backups).grid(row=4,column=0,columnspan=2,sticky='w',pady=8)
        button(self.profile_advanced,'Remove this slot',self._remove_profile).grid(row=5,column=0,columnspan=2,sticky='w',pady=8)
        label(self.profile_advanced,'Removing a slot keeps its save files and backups.',size=9,color=C['muted']).grid(row=6,column=0,columnspan=2,sticky='w',pady=8)
        self._refresh_backups()
        for variable in (self.profile_label,self.player,self.save_dir):variable.trace_add('write',lambda *_:self._save_profile() if not self._switching else None)

    def _toggle_profile_advanced(self):
        self.profile_advanced_visible=not self.profile_advanced_visible
        if self.profile_advanced_visible:self.profile_advanced.pack(fill='x')
        else:self.profile_advanced.pack_forget()
        self.profile_advanced_button.configure(text='Hide advanced save options' if self.profile_advanced_visible else 'Advanced save options')

    def _save_profile(self):
        if self._switching:return
        item=self._active_profile();item.update(label=self.profile_label.get().strip()[:40] or 'Game',player=self.player.get().strip()[:32] or 'Player',save_dir=self.save_dir.get().strip())
        selected=self.play_profiles.index(item);self.profile_picker['values']=[i['label'] for i in self.play_profiles];self.profile_picker.current(selected);self.active_slot.set('Save slot: '+item['label']);self._save();self._refresh_backups();self.status.set('Save slot settings saved automatically.')

    def _browse_save_dir(self):
        value=filedialog.askdirectory(title='Choose this profile’s save folder')
        if value:self.save_dir.set(value);self._save_profile()

    def _select_profile(self,event=None):
        index=self.profile_picker.current()
        if index<0:return
        self._save();self.active_profile_id=self.play_profiles[index]['id'];self._init_profiles();self._switching=True
        item=self._active_profile();self.profile_label.set(item['label']);self.player.set(item['player']);self.save_dir.set(item['save_dir'])
        values=prefs.defaults(self.root/'builds/current');values.update(self.preference_values);self.pause.set(values['pause']);self.filter.set(values['filter']);self.volume.set(values['volume']);self.area_scenery.set(values.get('area_scenery',False));self.companion_interactions.set(values['companion_interactions']);self.reduced_follower_motion.set(values.get('reduced_follower_motion',False));self.coop_exp_suppression.set(values.get('coop_exp_suppression',True));self._refresh_player_model_label()
        self.lan_slots.set(str(item.get('lan_slots',16)))
        self.connection_role.set(item['lan_role']);self.last_lan_action=item['lan_role'].lower()
        self.net_mode.set(item['network']['mode']);self.net_host.set(item['network']['host']);self.net_port.set(str(item['network']['port']));self.net_room.set(item['network']['room'])
        self._switching=False;self._save();self._refresh_backups();self.status.set('Selected '+item['label']+'.')

    def _new_profile(self):
        if len(self.play_profiles)>=16:self.status.set('Save slot limit reached (16).');return
        item=services.profile(rom=self.rom.get(),label='Save slot '+str(len(self.play_profiles)+1));item['save_dir']=str(self.home/'play-profiles'/item['id']/'saves');self.play_profiles.append(item)
        self.profile_picker['values']=[i['label'] for i in self.play_profiles];self.profile_picker.current(len(self.play_profiles)-1);self._select_profile()

    def _remove_profile(self):
        if len(self.play_profiles)==1:self.status.set('Keep at least one save slot.');return
        item=self._active_profile();self.play_profiles.remove(item);self.active_profile_id=self.play_profiles[0]['id'];self.profile_picker['values']=[i['label'] for i in self.play_profiles];self.profile_picker.current(0);self._select_profile();self.status.set('Save slot removed. Saves and backups were kept.')

    def _coop_page(self,parent):
        self._heading(parent,'PLAY TOGETHER','Co-op','Use matching builds and ROMs.')
        net=self._active_profile()['network'];self.net_mode=tk.StringVar(value=net['mode']);self.net_host=tk.StringVar(value=net['host']);self.net_port=tk.StringVar(value=str(net['port']));self.net_room=tk.StringVar(value=net['room'])
        first=card(parent);first.pack(fill='x',pady=(0,12))
        method=tk.Frame(first,bg=C['surface']);method.pack(fill='x',padx=18,pady=14)
        label(method,'Connection method',size=12,bold=True,bg=C['surface']).pack(anchor='w')
        picker=ttk.Combobox(method,textvariable=self.net_mode,values=['Local LAN','Tailscale backup','Internet UDP','Solo'],state='readonly');picker.pack(fill='x',pady=8)
        self.mode_help=tk.StringVar();label(method,textvariable=self.mode_help,size=10,color=C['muted'],bg=C['surface'],wraplength=590,justify='left').pack(anchor='w')
        self.mode_action=button(method,'Connection guide',self._connection_guide);self.mode_action.pack(anchor='w',pady=(8,0))
        self.net_mode.trace_add('write',lambda *_:self._connection_mode_changed());self._connection_mode_changed()
        second=card(parent);second.pack(fill='x',pady=(0,12))
        inner=tk.Frame(second,bg=C['surface']);inner.pack(fill='x',padx=18,pady=14);inner.columnconfigure(1,weight=1)
        label(inner,'Host or join',size=12,bold=True,bg=C['surface']).grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,10))
        roles=tk.Frame(inner,bg=C['surface']);roles.grid(row=1,column=0,columnspan=2,sticky='w')
        self.connection_role=tk.StringVar(value=self._active_profile()['lan_role']);self.last_lan_action=self.connection_role.get().lower()
        for role,text in [('Host','Host on this PC'),('Join','Join a friend')]:
            ttk.Radiobutton(roles,text=text,value=role,variable=self.connection_role,command=self._connection_role_changed).pack(side='left',padx=(0,16))
        self._field(inner,'Host address',self.net_host,2);self._field(inner,'Room name',self.net_room,3)
        label(inner,'Use your host’s IP and the same room name.',size=9,color=C['muted'],bg=C['surface'],wraplength=590,justify='left').grid(row=4,column=0,columnspan=2,sticky='w',pady=6)
        actions=tk.Frame(inner,bg=C['surface']);actions.grid(row=5,column=0,columnspan=2,sticky='w',pady=8)
        button(actions,'Save connection',self._save_connection,kind='primary').pack(side='left');self.connection_button=button(actions,'Test connection',self._check_connection);self.connection_button.pack(side='left',padx=8)
        self.connection_status=tk.StringVar(value='Not tested.')
        label(inner,textvariable=self.connection_status,size=10,color=C['muted'],bg=C['surface'],wraplength=590,justify='left').grid(row=6,column=0,columnspan=2,sticky='w',pady=6)
        self.connection_advanced=tk.Frame(inner,bg=C['surface']);self.connection_advanced.columnconfigure(1,weight=1)
        self._field(self.connection_advanced,'Sharing port',self.net_port,0)
        self.lan_slots=tk.StringVar(value=str(self._active_profile().get('lan_slots',16)))
        label(self.connection_advanced,'Lobby size',bg=C['surface']).grid(row=1,column=0,sticky='w')
        ttk.Combobox(self.connection_advanced,textvariable=self.lan_slots,values=list(range(2,17)),state='readonly',width=5).grid(row=1,column=1,sticky='w')
        server_actions=tk.Frame(self.connection_advanced,bg=C['surface']);server_actions.grid(row=2,column=0,columnspan=2,sticky='w',pady=8)
        button(server_actions,'Start sharing here',self._host_presence).pack(side='left');button(server_actions,'Stop sharing here',self._stop_presence).pack(side='left',padx=8)
        self.advanced_visible=False
        self.advanced_button=button(inner,'Advanced settings',self._toggle_connection_advanced);self.advanced_button.grid(row=7,column=0,columnspan=2,sticky='w',pady=4)
        native_actions=tk.Frame(parent,bg=C['background']);native_actions.pack(fill='x',pady=(0,12))
        self.lan_host_button=button(native_actions,'Host & play',lambda:self._start_lan('host'),kind='primary');self.lan_host_button.pack(side='left')
        self.lan_join_button=button(native_actions,'Join & play',lambda:self._start_lan('join'));self.lan_join_button.pack(side='left',padx=8)
        self.lan_retry_button=button(native_actions,'Retry',self._retry_lan);self.lan_retry_button.pack(side='left')
        self.lan_status=tk.StringVar(value='Choose a ROM on Play, then host or join here.')
        label(parent,textvariable=self.lan_status,size=10,color=C['muted'],wraplength=590,justify='left').pack(anchor='w',pady=(0,10))
        third=card(parent);third.pack(fill='x')
        label(third,'Next: join in-game',size=12,bold=True,bg=C['surface']).pack(anchor='w',padx=18,pady=(14,6))
        label(third,'Host & play starts a LAN lobby. Your friend uses Join & play.\nTurn C-Gear wireless and fast-forward off.',size=10,color=C['muted'],bg=C['surface'],wraplength=590,justify='left').pack(anchor='w',padx=18,pady=(0,14))
        readiness=card(parent);readiness.pack(fill='x',pady=(12,0))
        label(readiness,'Battle readiness',size=12,bold=True,bg=C['surface']).pack(anchor='w',padx=18,pady=(14,6))
        self.coop_checks=tk.StringVar(value='Run checks for this profile. Test connection above checks the presence relay. In-game readiness checks native LAN and partner agreement.')
        label(readiness,textvariable=self.coop_checks,size=10,bg=C['surface'],wraplength=590,justify='left').pack(anchor='w',padx=18,pady=6)
        button(readiness,'Check readiness',self._coop_readiness).pack(anchor='w',padx=18,pady=(6,14))

    def _coop_readiness(self):
        lines=self._run_checks()
        lines.insert(0,'BUILD: '+self._version_text())
        lines.append('PRESENCE: '+self.connection_status.get())
        lines.append('IN-GAME: Unova → Players checks protocol and ROM agreement; System → Multiplayer shows native LAN readiness.')
        self.coop_checks.set('\n'.join(lines))

    def _connection_mode_changed(self):
        mode=self.net_mode.get()
        self.mode_help.set({'Local LAN':'For computers on the same home network.','Tailscale backup':'Connect both PCs to the same Tailscale network.','Internet UDP':'Experimental. Requires a UDP server.','Solo':'Multiplayer off.'}.get(mode,''))
        self.mode_action.configure(text='Open internet setup' if mode=='Internet UDP' else 'Open Tailscale guide' if mode=='Tailscale backup' else 'Open play guide')

    def _connection_guide(self):
        if self.net_mode.get()=='Internet UDP':self._internet_wizard()
        else:self.guide('TAILSCALE_COOP.md' if self.net_mode.get()=='Tailscale backup' else 'PLAYER_GUIDE.md')

    def _connection_role_changed(self):
        item=self._active_profile()
        if self.connection_role.get()=='Host':
            if self.net_host.get().lower() not in ('localhost','127.0.0.1'):item['join_host']=self.net_host.get()
            self.net_host.set('127.0.0.1')
        else:self.net_host.set(item.get('join_host',''))
        if self.net_host.get():item['network']['host']=self.net_host.get()
        item['lan_role']=self.connection_role.get();self.last_lan_action=item['lan_role'].lower();self._save()

    def _toggle_connection_advanced(self):
        self.advanced_visible=not self.advanced_visible
        if self.advanced_visible:self.connection_advanced.grid(row=8,column=0,columnspan=2,sticky='ew')
        else:self.connection_advanced.grid_remove()
        self.advanced_button.configure(text='Hide advanced settings' if self.advanced_visible else 'Advanced settings')

    def _save_connection(self):
        try:
            value=services.network({'mode':self.net_mode.get(),'host':self.net_host.get(),'port':self.net_port.get(),'room':self.net_room.get()})
            self._active_profile()['lan_slots']=int(self.lan_slots.get())
            self._active_profile()['network']=value;self._active_profile()['lan_role']=self.connection_role.get()
            if self.connection_role.get()=='Join':self._active_profile()['join_host']=value['host']
            self._save()
            services.save_connection(self.root/'builds/current',value,self.player.get())
            self.status.set('Connection saved. The game applies it when no battle or trade is active.')
            self.connection_status.set('Saved '+value['host']+':'+str(value['port'])+' · reachability not checked.')
            return value
        except (OSError,ValueError) as exc:self.connection_status.set(str(exc));return None

    def _check_connection(self):
        value=self._save_connection()
        if value:self.connection_status.set('Checking presence relay…');self._worker('connection',lambda:services.check_relay(value,self._spawn_presence,self._restart_stale_presence))

    def _internet_wizard(self):
        try:
            path=self.root/'Online Co-op.cmd'
            if not path.is_file():raise ValueError('Internet helper missing. Use Repair game files.')
            os.startfile(str(path))
        except (OSError,ValueError) as exc:self.status.set(str(exc))

    def _host_presence(self):
        try:
            value=services.network({'mode':self.net_mode.get(),'host':'127.0.0.1','port':self.net_port.get(),'room':self.net_room.get()})
            self.net_host.set('127.0.0.1');self._save_connection()
            self.connection_status.set('Starting or checking the local relay…')
            self._worker('connection',lambda:services.check_relay(value,self._spawn_presence,self._restart_stale_presence))
        except (OSError,ValueError) as exc:self.connection_status.set(str(exc))

    def _restart_stale_presence(self,port):
        from .relay_process import RelayProcessError, stop_owned_listener
        try:stopped=stop_owned_listener(self.home,port)
        except RelayProcessError as exc:
            raise ValueError(str(exc)+' Stop the old relay manually, then check again.') from exc
        if not stopped:
            raise ValueError('An outdated relay is listening, but it was not started from this Unova Together installation. Stop it on the host, then check again.')
        self.presence_process=None
        self._spawn_presence(port)

    def _spawn_presence(self,port):
        if self.presence_process is not None and self.presence_process.poll() is None:
            return
        exe=self.root/'launcher/Pokemon Together.exe'
        if not exe.is_file():exe=self.root/'launcher/Unova Together.exe'
        command=[str(exe),'--presence-relay',str(port)] if getattr(sys,'frozen',False) else [sys.executable,str(HERE.parent/'unova_launcher.py'),'--presence-relay',str(port)]
        logs=self.home/'transfer';logs.mkdir(parents=True,exist_ok=True)
        with (logs/'presence-relay.log').open('ab') as log:
            self.presence_process=subprocess.Popen(command,cwd=self.root,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)

    def _stop_presence(self):
        if self.presence_process is not None and self.presence_process.poll() is None:
            self.presence_process.terminate();self.connection_status.set('Hosted relay stopped. Players can reconnect after it restarts.')
        else:self.connection_status.set('This launcher has no hosted relay to stop.')

    def _tools_page(self,parent):
        self._heading(parent,'KEEP PLAYING','Tools','Game checks, repair and read-only inspection.')
        button(parent,'Manage saves & backups',lambda:self.show_page('Profiles')).pack(anchor='w',pady=(0,10))
        self.preflight_text=tk.Text(parent,height=8,wrap='word',font=(F['body'],10),bg=C['surface'],fg=C['text'],relief='flat',padx=12,pady=10,state='disabled');self.preflight_text.pack(fill='x',pady=10)
        button(parent,'Run launch checks',self._run_checks).pack(anchor='w')
        button(parent,'Verify installed files',lambda:self._worker('integrity',lambda:services.integrity(self.root))).pack(anchor='w',pady=8)
        self.cleanup_button=button(parent,'Clean old installations',self._clean_installations);self.cleanup_button.pack(anchor='w',pady=8)
        label(parent,'Keeps your current build, one previous build, saves and backups.',size=9,color=C['muted'],wraplength=630,justify='left').pack(anchor='w')
        cleanup_panel=card(parent);cleanup_panel.pack(fill='x',pady=(12,16))
        label(cleanup_panel,'Cleanup progress',size=12,bold=True,bg=C['surface']).pack(anchor='w',padx=14,pady=(12,4))
        self.cleanup_eta=tk.StringVar(value='No cleanup in progress.')
        label(cleanup_panel,textvariable=self.cleanup_eta,size=9,color=C['muted'],bg=C['surface'],wraplength=650,justify='left').pack(anchor='w',padx=14,pady=(0,8))
        self.cleanup_bar=ttk.Progressbar(cleanup_panel,maximum=1,mode='determinate');self.cleanup_bar.pack(fill='x',padx=14,pady=(0,10),ipady=3)
        cleanup_log_frame=tk.Frame(cleanup_panel,bg=C['surface']);cleanup_log_frame.pack(fill='x',padx=14,pady=(0,14))
        self.cleanup_log=tk.Text(cleanup_log_frame,height=7,wrap='none',font=(F['utility'],9),bg=C['background'],fg=C['text'],relief='flat',padx=8,pady=6,state='disabled')
        cleanup_y=ttk.Scrollbar(cleanup_log_frame,orient='vertical',command=self.cleanup_log.yview)
        cleanup_x=ttk.Scrollbar(cleanup_panel,orient='horizontal',command=self.cleanup_log.xview)
        self.cleanup_log.configure(yscrollcommand=cleanup_y.set,xscrollcommand=cleanup_x.set)
        cleanup_y.pack(side='right',fill='y');self.cleanup_log.pack(side='left',fill='x',expand=True);cleanup_x.pack(fill='x',padx=14,pady=(0,10))
        self.cleanup_started=0.0;self.cleanup_total=0;self.cleanup_done=0
        actions=tk.Frame(parent,bg=C['background']);actions.pack(fill='x',pady=15)
        self.verify_button=button(actions,'Find repair download',self._find_repair);self.verify_button.pack(side='left')
        self.repair_button=button(actions,'Repair game files',self._repair);self.repair_button.pack(side='left',padx=8)
        label(parent,'Repair reinstalls game files. Saves are kept.',size=9,color=C['muted'],wraplength=630,justify='left').pack(anchor='w')
        self.export_button=button(parent,'Report a problem',self._export_diagnostics);self.export_button.pack(anchor='w',pady=15)
        self._refresh_backups()

        self._heading(parent,'READ-ONLY TOOLS','ROM & progression','Inspect the selected Redux game and compare party saves without changing them.')
        button(parent,'Check ROM compatibility',self._check_rom).pack(anchor='w',pady=8)
        self.xp_loss=tk.StringVar(value='0');self.xp_growth=tk.StringVar(value='Medium Slow')
        options=tk.Frame(parent,bg=C['background']);options.pack(fill='x',pady=8)
        label(options,'XP lost to co-op (%)',size=10).pack(side='left')
        ttk.Entry(options,textvariable=self.xp_loss,width=6).pack(side='left',padx=8)
        ttk.Combobox(options,textvariable=self.xp_growth,values=gen5_tools.GROWTH,state='readonly',width=18).pack(side='left')
        button(parent,'Calculate Challenge progression',self._calculate_progression).pack(anchor='w',pady=8)
        button(parent,'Compare two save files',self._compare_saves).pack(anchor='w',pady=8)
        self.tool_text=tk.Text(parent,height=15,wrap='word',font=('Consolas',10),bg=C['surface'],fg=C['text'],relief='flat',padx=12,pady=10,state='disabled');self.tool_text.pack(fill='x',pady=10)

    def _check_rom(self):
        rom=self._active_profile()['rom'];self._worker('tool-result',lambda:gen5_tools.compatibility(rom))

    def _automatic_cleanup(self):
        if self.busy:self.after(2000,self._automatic_cleanup);return
        self._start_storage_cleanup('storage-auto',recheck=False)

    def _clean_installations(self):
        if self.busy:return
        self.status.set('Cleaning old installations. Saves and backups are kept…')
        self._start_storage_cleanup('storage-clean',recheck=True)

    def _start_storage_cleanup(self,action,recheck):
        self.cleanup_started=time.monotonic();self.cleanup_total=0;self.cleanup_done=0
        self.cleanup_eta.set('Scanning old installations and checking file records… ETA will appear during removal.')
        self.cleanup_bar.stop();self.cleanup_bar.configure(mode='indeterminate',maximum=100,value=0);self.cleanup_bar.start(12)
        self.cleanup_log.configure(state='normal');self.cleanup_log.delete('1.0','end');self.cleanup_log.insert('end','Scanning for removable files…\n');self.cleanup_log.configure(state='disabled')
        def report(event):self.messages.put(('storage-progress',event))
        self._worker(action,lambda:storage.cleanup(self.home,recheck=recheck,progress=report))

    def _storage_progress(self,event):
        phase=event.get('phase');stage=event.get('stage')
        if phase=='scan':
            if stage=='checking':self.cleanup_eta.set(f"Scanning file records… {event.get('scanned',0)} checked; estimating work and ETA.")
            elif stage=='complete':self.cleanup_eta.set('No old installations need cleanup.')
            return
        if phase!='delete':return
        total=int(event.get('total',0));done=int(event.get('completed',0))
        if stage=='start':
            self.cleanup_bar.stop();self.cleanup_bar.configure(mode='determinate',maximum=max(1,total),value=0)
            self.cleanup_started=time.monotonic();self.cleanup_total=total;self.cleanup_done=0
            self.cleanup_eta.set(f'Checking and removing {total} verified file(s)… calculating ETA.')
        elif stage in ('deleted','checked','skipped'):
            self.cleanup_total=total;self.cleanup_done=done;self.cleanup_bar.configure(maximum=max(1,total),value=done)
            if total and done:
                elapsed=max(.001,time.monotonic()-self.cleanup_started);rate=done/elapsed;seconds=max(0,int((total-done)/rate))
                eta=f'{seconds//60}m {seconds%60:02d}s remaining' if seconds>=60 else f'{seconds}s remaining'
                self.cleanup_eta.set(f'Processed {done} of {total} files · ETA {eta}.')
            elif total:self.cleanup_eta.set(f'Processed {done} of {total} files · calculating ETA…')
            path=event.get('path')
            if path and stage in ('deleted','checked','skipped'):
                entry=('Deleted: ' if stage=='deleted' else 'Kept: ')+path
                if stage=='skipped' and event.get('reason'):entry+=' ('+event['reason']+')'
                elif stage=='checked':entry+=' (changed after the safety scan)'
                self.cleanup_log.configure(state='normal');self.cleanup_log.insert('end',entry+'\n');self.cleanup_log.see('end');self.cleanup_log.configure(state='disabled')
        elif stage=='directory':
            path=event.get('path')
            if path:
                self.cleanup_log.configure(state='normal');self.cleanup_log.insert('end','Removed empty folder: '+path+'\n');self.cleanup_log.see('end');self.cleanup_log.configure(state='disabled')
        elif stage=='complete':
            self.cleanup_bar.stop();self.cleanup_bar.configure(mode='determinate',maximum=max(1,total),value=max(1,total))
            self.cleanup_eta.set('Cleanup complete. '+('No verified files needed removal.' if total==0 else f'Processed {done} file(s).'))

    def _calculate_progression(self):
        rom=self._active_profile()['rom'];loss=self.xp_loss.get();growth=gen5_tools.GROWTH.index(self.xp_growth.get())
        self._worker('tool-result',lambda:gen5_tools.progression(rom,loss,growth))

    def _compare_saves(self):
        kinds=[('Save files','*.sav *.save *.dsv'),('All files','*.*')]
        first=filedialog.askopenfilename(parent=self,title='Choose the first Redux save',filetypes=kinds)
        if not first:return
        second=filedialog.askopenfilename(parent=self,title='Choose the second Redux save',filetypes=kinds)
        if second:self._worker('tool-result',lambda:gen5_tools.compare_saves(first,second))

    def _refresh_backups(self):
        item=self._active_profile();self.backup_paths=[];self.backup_picker['values']=[]
        self.backup_picker.set('Checking backups…');self.restore_button.configure(state='disabled')
        self.profile_game.set('Game: '+(Path(item['rom']).name if item['rom'] else 'Choose a ROM on Play to get started.'));self.active_slot.set('Save slot: '+item['label'])
        backup_error=save_error=None;count=None
        try:backup_paths=services.backups(self.home,item)
        except OSError as exc:backup_paths=[];backup_error=exc
        try:count=len(services.save_files(item))
        except OSError as exc:save_error=exc
        self.backup_paths=backup_paths;self.backup_picker['values']=[services.backup_label(p) for p in backup_paths]
        if backup_paths:self.backup_picker.current(0)
        elif backup_error:self.backup_picker.set('Backups unavailable')
        else:self.backup_picker.set('No backups yet — select Back up now')
        if backup_error or save_error:
            self.save_summary.set(('Could not read this profile’s save folder. Check folder access.' if save_error else
                f'{count} save file(s) found. Could not list backups; check folder access.'))
            errors=[]
            if backup_error:errors.append('backups: '+str(backup_error))
            if save_error:errors.append('saves: '+str(save_error))
            self.status.set('Could not inspect this profile’s files ('+'; '.join(errors)+').')
            return False
        self.save_summary.set(f'{count} save file(s) found · {len(backup_paths)} backup(s). Save in-game before backing up.' if count else 'No save yet. Play, save in-game, then return here to back it up.')
        set_enabled(self.restore_button,bool(backup_paths));return True

    def _backup_now(self):
        try:
            path=services.backup(self.home,self._active_profile());self.status.set('Save backup created.' if path else 'No .sav/.save/.dsv files found for this profile.');self._refresh_backups()
        except (OSError,ValueError) as exc:self.status.set(str(exc))

    def _restore_backup(self):
        try:
            if prefs.any_running():raise ValueError('Close all melonDS instances before restoring saves.')
            index=self.backup_picker.current()
            if not 0<=index<len(self.backup_paths):raise ValueError('Select a save backup first.')
            count=services.restore(self.home,self._active_profile(),self.backup_paths[index]);self.status.set(f'Restored {count} save file(s). Previous saves were backed up.');self._refresh_backups()
        except (OSError,ValueError,KeyError,zipfile.BadZipFile) as exc:self.status.set(str(exc))

    def _open_backups(self):
        path=self.home/'save-backups'
        try:
            path.mkdir(exist_ok=True)
            os.startfile(str(path))
        except OSError as exc:self.status.set('Could not open backups folder: '+str(exc))

    def _run_checks(self):
        try:lines=services.checks(self.root,self._active_profile())
        except (OSError,ValueError) as exc:lines=['BLOCK: '+str(exc)]
        self.preflight_text.configure(state='normal');self.preflight_text.delete('1.0','end');self.preflight_text.insert('1.0','\n'.join(lines));self.preflight_text.configure(state='disabled')
        self.status.set('Launch checks complete. In-game checks are listed explicitly.')
        return lines

    def _find_repair(self):
        self.status.set('Looking for this version’s official repair download…')
        def find():
            target=updates.installed_version(self.home)
            return updates.select_latest([r for r in updates.fetch_releases() if target==(0,0,0) or r.get('tag_name','').lstrip('v')=='.'.join(map(str,target))])
        self._worker('repair-feed',find)

    def _install_with_backup(self,release):
        # Updates and repairs install into a fresh versioned folder. Keep the
        # current game usable while staging; its runtime and saves are untouched.
        for item in self.play_profiles:services.backup(self.home,item,'before-update')
        return updates.install(self.home,release,self.cancel,lambda done,total:self.messages.put(('progress',done*100/total)))

    def _repair(self):
        if not self.repair_release:return
        release=dict(self.repair_release);release['_repair']=True;self.show_page('Updates');self.status.set('Backing up saves and repairing game files…');self._worker('installed',lambda:self._install_with_backup(release))

    def _export_diagnostics(self):
        value=filedialog.asksaveasfilename(title='Report a problem',defaultextension='.zip',initialfile='Unova-Together-diagnostics.zip',filetypes=[('ZIP archive','*.zip')])
        if value:self._worker('diagnostics',lambda:services.diagnostics(self.root,Path(value),self.home))

    def _review_report(self,path):
        window=tk.Toplevel(self);window.title('Review problem report');window.geometry('760x540')
        label(window,'Review before sharing',size=18,bold=True).pack(anchor='w',padx=16,pady=12)
        label(window,'Logs are redacted. No ROMs, saves or RAM dumps. Nothing is uploaded.',size=10,wraplength=700).pack(anchor='w',padx=16)
        text=tk.Text(window,wrap='word',font=(F['utility'],10));text.pack(fill='both',expand=True,padx=16,pady=12)
        with zipfile.ZipFile(path) as bundle:
            for name in bundle.namelist():
                data=bundle.read(name)
                text.insert('end',name+'\n'+data[:8192].decode('utf-8',errors='replace')+('\n[Preview shortened. Open the ZIP to review this file in full.]' if len(data)>8192 else '')+'\n\n')
        text.configure(state='disabled')
        controls=tk.Frame(window,bg=C['background']);controls.pack(fill='x',padx=16,pady=12)
        button(controls,'Open report folder',lambda:self._open_report_folder(path.parent)).pack(side='left')
        button(controls,'Open GitHub issues',lambda:webbrowser.open('https://github.com/'+updates.REPO+'/issues')).pack(side='left',padx=8)
        button(controls,'Close',window.destroy).pack(side='right')

    def _open_report_folder(self,path):
        try:os.startfile(str(path))
        except OSError as exc:self.status.set('Could not open report folder: '+str(exc))

    def _apply_save_folder(self,runtime,item,default_directory=None):
        doc=prefs.read_document(runtime);value=item.get('save_dir','')
        if not value and default_directory:value=str(default_directory)
        if value:
            folder=Path(value).expanduser().resolve();folder.mkdir(parents=True,exist_ok=True);value=str(folder)
        for key in [k for k in doc if re.fullmatch(r'Instance\d+',k)] or ['Instance0']:
            doc.setdefault(key,tomlkit.table())['SaveFilePath']=value
        prefs.atomic(Path(runtime)/'melonDS.toml',tomlkit.dumps(doc))

    def _settings_page(self,parent):
        self._heading(parent,'MAKE IT YOURS','Settings','Applies next launch.')
        general=card(parent);general.pack(fill='x',pady=(0,18))
        box=tk.Frame(general,bg=C['surface']);box.pack(fill='x',padx=18,pady=16)
        label(box,'LAUNCHER & GAME',size=9,bold=True,bg=C['surface']).pack(anchor='w',pady=(0,10))
        ttk.Checkbutton(box,text='Check for updates on startup',variable=self.auto,command=self._save).pack(anchor='w',pady=4)
        values=prefs.defaults(self.root/'builds/current');values.update(self.preference_values)
        self.pause=tk.BooleanVar(value=values['pause']);self.filter=tk.BooleanVar(value=values['filter'])
        self.volume=tk.IntVar(value=values['volume'])
        ttk.Checkbutton(box,text='Pause when unfocused (off for co-op)',variable=self.pause,
            command=lambda:self._preference('pause',self.pause.get())).pack(anchor='w',pady=4)
        ttk.Checkbutton(box,text='Smooth display filtering',variable=self.filter,
            command=lambda:self._preference('filter',self.filter.get())).pack(anchor='w',pady=4)
        self.area_scenery=tk.BooleanVar(value=values.get('area_scenery',False))
        ttk.Checkbutton(box,text='Nearby battle scenery (experimental)',variable=self.area_scenery,
            command=lambda:self._preference('area_scenery',self.area_scenery.get())).pack(anchor='w',pady=4)
        label(box,'Tab / Shift+Tab: move focus · Enter: select · Ctrl+Tab: change page.\nController: D-pad / stick to move, A to select, B to return, LB / RB to change page.',size=9,color=C['muted'],bg=C['surface'],wraplength=620,justify='left').pack(anchor='w',pady=8)
        label(box,'Game volume',size=10,bg=C['surface']).pack(anchor='w',pady=(10,0))
        self.volume_slider=tk.Scale(box,from_=0,to=100,orient='horizontal',variable=self.volume,showvalue=True,
            bg=C['surface'],fg=C['text'],highlightthickness=0,relief='flat',length=320,takefocus=True,
            command=lambda v:self._preference('volume',int(float(v))))
        self.volume_slider.pack(anchor='w')
        button(box,'All emulator settings',self._all_settings).pack(anchor='w',pady=(12,0))
        label(box,'Controls, display, audio and more.',size=9,color=C['muted'],bg=C['surface'],wraplength=620,justify='left').pack(anchor='w',pady=8)
        coop_test=card(parent);coop_test.pack(fill='x',pady=(0,18))
        coop_test_box=tk.Frame(coop_test,bg=C['surface']);coop_test_box.pack(fill='x',padx=18,pady=16)
        label(coop_test_box,'CO-OP TESTING',size=9,bold=True,bg=C['surface']).pack(anchor='w',pady=(0,8))
        self.coop_exp_suppression=tk.BooleanVar(value=values.get('coop_exp_suppression',True))
        ttk.Checkbutton(coop_test_box,text='Suppress EXP in co-op battles (testing)',variable=self.coop_exp_suppression,
            command=lambda:self._preference('coop_exp_suppression',self.coop_exp_suppression.get())).pack(anchor='w',pady=4)
        label(coop_test_box,'Skips EXP, level-up and move-learning rewards during co-op test/story battles. On by default; turn it off to test normal EXP rewards. Applies on the next launch.',size=9,color=C['muted'],bg=C['surface'],wraplength=620,justify='left').pack(anchor='w',pady=(2,0))
        followers=card(parent);followers.pack(fill='x',pady=(0,18))
        follower_box=tk.Frame(followers,bg=C['surface']);follower_box.pack(fill='x',padx=18,pady=16)
        label(follower_box,'FOLLOWING POKÉMON',size=9,bold=True,bg=C['surface']).pack(anchor='w',pady=(0,8))
        self.companion_interactions=tk.BooleanVar(value=values['companion_interactions'])
        ttk.Checkbutton(follower_box,text='Companion interactions',variable=self.companion_interactions,
            command=lambda:self._preference('companion_interactions',self.companion_interactions.get())).pack(anchor='w',pady=4)

        label(follower_box,'On by default. Stop, face your follower and press R+A, or tap it. Changes apply next launch.\nShow or hide followers in Unova → Settings.',size=9,color=C['muted'],bg=C['surface'],wraplength=620,justify='left').pack(anchor='w',pady=(6,0))
        self.reduced_follower_motion=tk.BooleanVar(value=values.get('reduced_follower_motion',False))
        ttk.Checkbutton(follower_box,text='Reduced follower motion',variable=self.reduced_follower_motion,
            command=lambda:self._preference('reduced_follower_motion',self.reduced_follower_motion.get())).pack(anchor='w',pady=(8,4))
        label(follower_box,'Keeps reaction symbols; disables decorative bobbing and reaction movement.',size=9,color=C['muted'],bg=C['surface'],wraplength=620,justify='left').pack(anchor='w')
        appearance=card(parent);appearance.pack(fill='x',pady=(0,18))
        appearance_box=tk.Frame(appearance,bg=C['surface']);appearance_box.pack(fill='x',padx=18,pady=16)
        label(appearance_box,'PLAYER APPEARANCE',size=9,bold=True,bg=C['surface']).pack(anchor='w')
        self.player_model_label=tk.StringVar()
        self._refresh_player_model_label()
        label(appearance_box,textvariable=self.player_model_label,size=11,bold=True,bg=C['surface']).pack(anchor='w',pady=(8,4))
        button(appearance_box,'Choose a field character',self._choose_player_model).pack(anchor='w',pady=(6,8))
        label(appearance_box,'Choose from animated characters stored in your ROM. This changes your walking character; bike and surf forms keep their normal game animations. Applies next launch.',size=9,color=C['muted'],bg=C['surface'],wraplength=620,justify='left').pack(anchor='w')
        cheats=card(parent);cheats.pack(fill='x')
        box=tk.Frame(cheats,bg=C['surface']);box.pack(fill='x',padx=18,pady=16)
        label(box,'OPTIONAL CHEATS',size=9,bold=True,bg=C['surface']).pack(anchor='w')
        self.cheat_status=label(box,'Choose a ROM on Play to check compatibility.',size=10,color=C['muted'],bg=C['surface'],wraplength=620,justify='left')
        self.cheat_status.pack(anchor='w',pady=(8,12))
        self.cheat_vars={};self.cheat_buttons={}
        for item in prefs.CATALOG['codes']:
            variable=tk.BooleanVar(value=False);self.cheat_vars[item['id']]=variable
            control=ttk.Checkbutton(box,text=item['name']+' · '+item['activation'],variable=variable,
                command=lambda ident=item['id']:self._cheat_changed(ident))
            control.pack(anchor='w',pady=(8,3));self.cheat_buttons[item['id']]=control
            label(box,item['note'],size=9,color=C['muted'],bg=C['surface'],wraplength=620,justify='left').pack(anchor='w',padx=22)
        label(box,'Disable cheats after use. Saved changes are permanent.',
            size=9,color=C['muted'],bg=C['surface'],wraplength=620,justify='left').pack(anchor='w',pady=(15,8))
        button(box,'Code sources & licenses',self.cheat_sources).pack(anchor='w')

    def _preference(self,key,value):
        self.preference_values[key]=value;self._save()

    def _refresh_player_model_label(self):
        model_id=self.preference_values.get('player_model',0)
        self.player_model_label.set('Default character' if model_id==0 else player_models.display_name(model_id))

    def _choose_player_model(self):
        source=Path(self.rom.get())
        if not source.is_file() or source.suffix.lower()!='.nds':
            self.status.set('Choose a supported Redux game on Play before selecting a character.');return
        window=tk.Toplevel(self);window.title('Choose field character');window.geometry('460x540');window.minsize(360,420);window.transient(self)
        outer=tk.Frame(window,bg=C['background']);outer.pack(fill='both',expand=True,padx=16,pady=16)
        label(outer,'Choose an animated character',size=16,bold=True,bg=C['background']).pack(anchor='w')
        label(outer,'Search by name or model number. Characters are read from the selected ROM.',size=9,color=C['muted'],bg=C['background'],wraplength=420,justify='left').pack(anchor='w',pady=(6,12))
        query=tk.StringVar();entry=tk.Entry(outer,textvariable=query,font=(F['body'],11),highlightthickness=2,highlightcolor=C['focus']);entry.pack(fill='x',pady=(0,10))
        body=tk.Frame(outer,bg=C['surface']);body.pack(fill='both',expand=True)
        choices=tk.Listbox(body,font=(F['body'],11),bg=C['surface'],fg=C['text'],selectbackground=C['primary'],selectforeground=C['surface'],activestyle='none',exportselection=False,relief='flat',highlightthickness=0)
        scroll=ttk.Scrollbar(body,command=choices.yview);scroll.pack(side='right',fill='y');choices.configure(yscrollcommand=scroll.set);choices.pack(fill='both',expand=True)
        state=label(outer,'Reading character models…',size=9,color=C['muted'],bg=C['background']);state.pack(anchor='w',pady=(8,6))
        actions=tk.Frame(outer,bg=C['background']);actions.pack(fill='x',pady=(8,0))
        result_queue=queue.Queue();models=[];visible=[];ready=False
        def load_models():
            try:result_queue.put(('models',player_models.list_models(source)))
            except Exception as exc:result_queue.put(('error',str(exc)))
        threading.Thread(target=load_models,daemon=True).start()
        def populate(*_):
            nonlocal visible
            term=query.get().strip().casefold();current=choices.curselection();selected=visible[current[0]] if current else None
            visible=[model for model in models if not term or term in player_models.display_name(model).casefold() or term in str(model)]
            choices.delete(0,'end')
            for model in visible:choices.insert('end',player_models.display_name(model))
            if selected in visible:
                index=visible.index(selected);choices.selection_set(index);choices.see(index)
        def apply_selection():
            if not ready:return
            selected=choices.curselection()
            if not selected:return
            self.preference_values['player_model']=visible[selected[0]];self._refresh_player_model_label();self._save()
            self.status.set('Character saved · applies next launch.');window.destroy()
        def use_default():
            self.preference_values['player_model']=0;self._refresh_player_model_label();self._save()
            self.status.set('Default character selected · applies next launch.');window.destroy()
        def poll_catalog():
            nonlocal ready
            if not window.winfo_exists():return
            try:
                kind,value=result_queue.get_nowait();ready=True
                if kind=='error':state.configure(text='Could not read models: '+str(value))
                else:
                    models.extend(value);populate();state.configure(text=f'{len(models)} animated characters available.');entry.focus_set()
            except queue.Empty:window.after(100,poll_catalog)
        query.trace_add('write',populate)
        choices.bind('<Double-Button-1>',lambda _event:apply_selection())
        button(actions,'Default character',use_default).pack(side='left')
        button(actions,'Use selected',apply_selection,kind='primary').pack(side='right')
        poll_catalog()

    def _all_settings(self):
        from .settings_editor import SettingsEditor
        try:SettingsEditor(self,self.root/'builds/current')
        except (OSError,ValueError,tomlkit.exceptions.ParseError) as exc:self.status.set('Could not open emulator settings: '+str(exc))

    def _cheat_changed(self,ident):
        if not self.profile:return
        self.cheat_choices.setdefault(self.profile['key'],{})[ident]=self.cheat_vars[ident].get()
        self._save();self.status.set('Cheat choice saved · applies on next launch.')

    def _rom_changed(self):
        if self.rom_timer is not None:
            try:self.after_cancel(self.rom_timer)
            except tk.TclError:pass
        self.profile=None
        for control in self.cheat_buttons.values():control.state(['disabled'])
        self.cheat_status.configure(text='Checking ROM compatibility…' if self.rom.get() else 'Choose a ROM on Play to check compatibility.')
        self.rom_timer=self.after(250,self._identify_rom);self._sync()

    def _identify_rom(self):
        self.rom_timer=None;self.profile=prefs.identify(self.rom.get())
        choices=self.cheat_choices.get(self.profile['key'],{}) if self.profile else {}
        for ident,control in self.cheat_buttons.items():
            control.state(['!disabled'] if self.profile else ['disabled']);self.cheat_vars[ident].set(bool(choices.get(ident,False)))
        text=('Compatible: '+self.profile['profile']+' · off unless selected.' if self.profile else
            'Cheats unavailable for this game file. Reviewed: Blaze Black 2 Redux Complete v1.4.1. You can still play normally.')
        self.cheat_status.configure(text=text)

    def cheat_sources(self):
        try:os.startfile(str(HERE/'assets/CHEATS-SOURCES.md'))
        except OSError as exc:self.status.set('Could not open code sources: '+str(exc))

    @staticmethod
    def cheat_vars_ids():return {item['id'] for item in prefs.CATALOG['codes']}

    def _read_settings(self):
        try:
            if self.config_path.stat().st_size>65536:return
            data=json.loads(self.config_path.read_text(encoding='utf-8'))
            if data.get('selected_game') in game_routes.GAMES.values():self.selected_game.set(data['selected_game'])
            for key,var in (('research_root',self.research_root),('research_address',self.research_address)):
                if isinstance(data.get(key),str) and len(data[key])<4096:var.set(data[key])
            if data.get('research_mode') in game_routes.MODES:self.research_mode.set(data['research_mode'])
            if isinstance(data.get('rom'),str):self.rom.set(data['rom'])
            if isinstance(data.get('profiles'),list):self.play_profiles=[services.normalize(i) for i in data['profiles'][:16] if isinstance(i,dict) and re.fullmatch(r'[a-f0-9]{32}',str(i.get('id',''))) and isinstance(i.get('rom'),str)]
            self.active_profile_id=str(data.get('active_profile',''))
            if type(data.get('check')) is bool:self.auto.set(data['check'])
            if type(data.get('music')) is bool:self.music.set(data['music'])
            if isinstance(data.get('preferences'),dict):self.preference_values={k:v for k,v in data['preferences'].items() if (k in ('pause','filter','area_scenery','companion_interactions','reduced_follower_motion','coop_exp_suppression') and type(v) is bool) or (k=='volume' and type(v) is int and 0<=v<=100) or (k=='player_model' and type(v) is int and 0<=v<=65535)}
            if isinstance(data.get('cheats'),dict):self.cheat_choices={k:{ident:flag for ident,flag in v.items() if ident in self.cheat_vars_ids() and type(flag) is bool} for k,v in list(data['cheats'].items())[-32:] if isinstance(k,str) and len(k)<=32 and isinstance(v,dict)}
        except (OSError,ValueError,AttributeError):pass

    def _save(self):
        if self._switching:return
        if self.play_profiles:
            item=self._active_profile();item['rom']=self.rom.get();item['preferences']=dict(self.preference_values)
        try:
            prefs.atomic(self.config_path,json.dumps({'selected_game':self.selected_game.get(),'research_root':self.research_root.get(),'research_mode':self.research_mode.get(),'research_address':self.research_address.get(),'rom':self.rom.get(),'check':self.auto.get(),'music':self.music.get(),'preferences':self.preference_values,'cheats':self.cheat_choices,'profiles':self.play_profiles,'active_profile':self.active_profile_id}))
        except OSError as exc:self.status.set('Could not save settings: '+str(exc))

    def _sync(self):
        self.library_details['black2'].set(self._version_text())
        path=Path(self.rom.get());valid=path.is_file() and path.suffix.lower()=='.nds';running=self._game_is_running()
        present=(self.root/'builds/current/melonDS.exe').is_file()
        set_enabled(self.research_play,not self.busy,'primary')
        for control in self.library_buttons.values():set_enabled(control,not self.busy,'primary')
        for control in self.research_launch_buttons:set_enabled(control,not self.busy,'primary')
        set_enabled(self.play,valid and not self.busy and not running and present,'primary')
        set_enabled(self.lan_host_button,valid and not self.busy and not running and present and self.net_mode.get()!='Solo','primary')
        set_enabled(self.lan_retry_button,valid and not self.busy and present and self.net_mode.get()!='Solo')
        set_enabled(self.lan_join_button,valid and not self.busy and not running and present and self.net_mode.get()!='Solo')
        set_enabled(self.check_button,not self.busy);set_enabled(self.refresh_news,not self.busy)
        set_enabled(self.update_button,bool(self.release) and not self.busy,'primary')
        set_enabled(self.connection_button,not self.busy);set_enabled(self.verify_button,not self.busy);set_enabled(self.export_button,not self.busy)
        set_enabled(self.repair_button,bool(self.repair_release) and not self.busy)
        set_enabled(self.cancel_button,self.busy and self.operation=='installed' and not self.cancel.is_set())
        set_enabled(self.backup_button,not self.busy,'primary');set_enabled(self.restore_button,bool(self.backup_paths) and not self.busy and not running)
        set_enabled(self.cleanup_button,not self.busy)
        message=('Game running. Save normally and close it before starting another session.' if running else 'Emulator missing. Extract the complete release folder.' if not present else
            'Requires Blaze Black 2 Redux Complete v1.4.1. Use a patch only when it is listed for your exact Redux version.' if not self.rom.get() else 'Game file not found. Browse to an existing .nds file.' if not valid else 'Game file selected. Use a supported Redux version to play.')
        self.game_hint.configure(text=message)

    def _game_is_running(self):
        child=self.game is not None and self.game.poll() is None
        now=time.monotonic()
        if now>=self._process_check_at:
            self._process_running=prefs.running_in_home(self.home)
            self._process_check_at=now+1.0
        return child or self._process_running

    def _stop_game_workers(self,timeout=.5):
        for name in ('surroundings_worker',):
            worker=getattr(self,name,None)
            if worker is None:continue
            stop=getattr(worker,'stop',None)
            if hasattr(stop,'set'):stop.set()
            thread=getattr(worker,'thread',None)
            if thread is not None and callable(getattr(thread,'join',None)):
                thread.join(timeout=max(0.,float(timeout)))
            setattr(self,name,None)

    def _reap_game_workers(self):
        if self.game is not None and self.game.poll() is not None:
            self._stop_game_workers()

    def _game_selected(self,save=True):
        mod=next((key for key,spec in game_routes.MODS.items() if spec['game']==self.selected_game.get()),None)
        if mod is None:return
        self._open_mod(mod,save=save)

    def _open_mod(self,mod,save=True):
        if self.busy:self.status.set('Wait for the current operation before changing mods.');return
        if mod not in game_routes.MODS:return
        self.active_mod=mod;self.selected_game.set(game_routes.MODS[mod]['game'])
        self._apply_navigation();self.show_page(game_routes.MODS[mod]['pages'][0])
        self.nav[self.page_name].focus_set()
        self.status.set('')
        if save:self._save()
        self._sync()
        if mod=='black2' and not self.unova_started and not self.testing:
            self.unova_started=True
            if self.auto.get():self.after(300,lambda:self.check() if self.active_mod=='black2' else None)
            self.after(600,lambda:self.refresh_guides() if self.active_mod=='black2' else None)

    def _apply_navigation(self):
        self.visible_pages=('Library',)+game_routes.MODS[self.active_mod]['pages'] if self.active_mod else ('Library',)
        for name,control in self.nav.items():
            control.pack_forget()
            if name in self.visible_pages:control.pack(fill='x',padx=12,pady=2)
        self.mod_caption.configure(text=game_routes.MODS[self.active_mod]['name'] if self.active_mod else 'MULTIPLAYER MODS')
        self.footer_version.configure(text=self._version_text() if self.active_mod=='black2' else 'Pokemon X · Prototype' if self.active_mod else 'Multiplayer mod library')

    def _return_library(self):
        if self.busy:self.status.set('Wait for the current operation before changing mods.');return
        self.active_mod=None;self._apply_navigation();self.show_page('Library')
        self.status.set('');self.nav['Library'].focus_set()

    def _browse_research(self):
        path=filedialog.askdirectory(title='Choose prepared Pokemon X co-op folder')
        if path:self.research_root.set(path);self._save();self._sync()

    def _launch_research(self,mode=None):
        if self.busy:return
        selected=mode or game_routes.MODES[self.research_mode.get()]
        research_root=self.research_root.get();research_address=self.research_address.get()
        try:game_routes.research_command(research_root,selected,research_address)
        except (OSError,ValueError) as error:self.status.set(str(error));return
        self._save();self.status.set('Starting Pokemon X co-op...')
        self._worker('research-launch',lambda:game_routes.launch_research(research_root,selected,research_address))

    def browse(self):
        path=filedialog.askopenfilename(title='Choose your Blaze Black 2 Redux game file',filetypes=[('Nintendo DS game file','*.nds')])
        if path:self.rom.set(path);self._save()

    def _start_lan(self,action):
        if self.selected_game.get()==game_routes.GAMES['pokemon-x']:self._launch_research('host' if action=='host' else 'guest');return
        if self.busy or self._game_is_running():return
        if self.net_mode.get()=='Solo':self.lan_status.set('Choose LAN or an online mode first.');return
        self.connection_role.set('Host' if action=='host' else 'Join')
        if action=='host':self._connection_role_changed()
        self.last_lan_action=action;self._active_profile()['lan_role']=self.connection_role.get()
        value=self._save_connection()
        if value:
            self.lan_status.set('Checking player sharing…')
            self._worker('lan-'+action,lambda:services.check_relay(value,self._spawn_presence,self._restart_stale_presence))

    def launch(self,lan_action=None):
        if self.selected_game.get()==game_routes.GAMES['pokemon-x']:self._launch_research('host' if lan_action=='host' else 'guest' if lan_action=='join' else None);return
        if self.busy:return
        if self._game_is_running():self.status.set('This game is already running from this installation.');return
        if lan_action is not None:
            if lan_action not in ('host','join'):raise ValueError('Unknown LAN action')
            if self.net_mode.get()=='Solo':self.lan_status.set('Choose LAN or an online mode first.');return
            if not self.player.get().strip() or len(self.player.get().strip().encode('utf-8'))>31:self.lan_status.set('Player name must fit within 31 UTF-8 bytes.');return
        path=Path(self.rom.get())
        if not path.is_file() or path.suffix.lower()!='.nds':return
        self._save_profile()
        if self._save_connection() is None:self.show_page('Co-op');return
        self._save()
        if any(line.startswith('BLOCK:') for line in self._run_checks()):self.show_page('Tools');return
        try:
            exe=self.root/'builds/current/melonDS.exe'
            self._identify_rom()
            selected=self.cheat_choices.get(self.profile['key'],{}) if self.profile else {}
            item=self._active_profile();net=services.network(item['network'])
            settings=dict(self.preference_values);settings['pause']=False if net['mode']!='Solo' else settings.get('pause',False)
            model_id=settings.pop('player_model',0)
            try:
                self.status.set('Preparing Cynthia’s Route 7 story event…');self.update_idletasks()
                launch_rom=cynthia_event.prepare_variant(path,self.home)
            except cynthia_event.UnsupportedRomError as exc:
                launch_rom=path
                self.status.set(str(exc)+' The game will start without the Route 7 event.')
            if model_id:launch_rom=player_models.prepare_variant(launch_rom,self.home,model_id)
            prefs.apply(exe.parent,path,settings,selected,self.profile,self.home)
            self._apply_save_folder(exe.parent,item,default_directory=path.parent if (model_id or launch_rom != path) else None)
            env=dict(os.environ);env.update({'UNOVA_PLAYER_NAME':item['player'],'UNOVA_RELAY_HOST':net['host'],'UNOVA_RELAY_PORT':str(net['port']),'UNOVA_RELAY_ROOM':net['room'],'UNOVA_TRAINER_COOP':'0' if net['mode']=='Solo' else '1','UNOVA_AUTO_CONNECT':'0' if net['mode']=='Solo' else '1'})
            companion='1' if settings.get('companion_interactions',True) else '0'
            env['UNOVA_COMPANION_INTERACTIONS']=companion
            env['UNOVA_EXPERIMENTAL_COMPANION']=companion # compatibility with existing released runtimes
            env['UNOVA_FOLLOWER_REDUCED_MOTION']='1' if settings.get('reduced_follower_motion',False) else '0'
            env['UNOVA_COOP_EXP_SUPPRESSION']='1' if settings.get('coop_exp_suppression',True) else '0'
            self._stop_game_workers()
            env.pop('UNOVA_AREA_CATALOG',None)
            env.pop('UNOVA_SURROUNDINGS_DIR',None)
            if settings.get('area_scenery',False):
                from area_scene_cache import prepare_catalog
                self.status.set('Preparing battle scenery…');self.update_idletasks()
                env['UNOVA_AREA_CATALOG']=str(prepare_catalog(path,self.home/'area-scenes'))
                from battle_surroundings_worker import SurroundingsWorker
                directory=Path(env['UNOVA_AREA_CATALOG']).parent/'nearby'
                self.surroundings_worker=SurroundingsWorker(path,directory)
                env['UNOVA_SURROUNDINGS_DIR']=str(directory)
            for key in ('UNOVA_LAN_ACTION','UNOVA_LAN_HOST','UNOVA_LAN_REQUEST','UNOVA_LAN_SLOTS'):env.pop(key,None)
            self.lan_request=''
            if lan_action:
                self.lan_request=uuid.uuid4().hex;self.lan_started=time.monotonic();self.lan_was_connected=False
                env.update({'UNOVA_LAN_ACTION':lan_action,'UNOVA_LAN_HOST':net['host'],'UNOVA_LAN_REQUEST':self.lan_request,'UNOVA_LAN_SLOTS':str(item.get('lan_slots',16))})
                self.lan_status.set('Starting LAN host…' if lan_action=='host' else 'Joining LAN host…')
            self._stop_music()
            self.game=subprocess.Popen([str(exe),str(launch_rom.resolve())],cwd=exe.parent,env=env)
            self.status.set('Game running. Save normally and close it before starting another session.');self._sync()
        except (OSError,ValueError,subprocess.SubprocessError) as exc:
            self._stop_game_workers();self.status.set('Unable to start the game: '+str(exc))

    def guide(self,name='PLAYER_GUIDE.md'):
        if name not in services.GUIDES:return
        guide=services.cached_guide(self.home,name) or self.root/'docs'/name
        try:
            if guide.is_file():os.startfile(str(guide))
            else:webbrowser.open('https://github.com/'+updates.REPO+'/blob/main/docs/'+name)
        except OSError as exc:self.status.set('Could not open the guide: '+str(exc))

    def refresh_guides(self):
        if self.guides_busy:return
        self.guides_busy=True;self.guide_status.set('Checking GitHub guides…')
        def run():
            try:self.messages.put(('guides',services.refresh_guides(self.home)))
            except Exception:self.messages.put(('guides-offline',None))
        threading.Thread(target=run,daemon=True).start()

    def _worker(self,action,task):
        if self.busy:return
        self.busy=True;self.operation=action;self.cancel.clear();self._sync()
        def run():
            try:self.messages.put((action,task()))
            except Exception as exc:self.messages.put(('error',str(exc)))
        threading.Thread(target=run,daemon=True).start()

    def check(self):
        if self.busy:return
        self.status.set('Checking official GitHub releases…');self.update_status.set('Checking GitHub…');self.news_status.set('Refreshing patch notes from GitHub…')
        self._worker('feed',updates.launcher_feed)

    def install_update(self):
        if not self.release or self.busy:return
        self.show_page('Updates');self.status.set('Downloading and verifying update…');self.update_status.set('Downloading release '+self.release['version']+'…')
        self.phase.set('Downloading · verification follows');self.bar['value']=0;release=dict(self.release)
        self._worker('installed',lambda:self._install_with_backup(release))

    def cancel_download(self):
        if self.busy and self.operation=='installed':self.cancel.set();self.phase.set('Cancelling · current build remains active');self._sync()

    def _poll(self):
        try:
            while True:
                action,value=self.messages.get_nowait()
                if action in ('guides','guides-offline'):
                    self.guides_busy=False;self.guide_status.set('Guides up to date' if action=='guides' else 'Offline · using saved guides');continue
                if action=='storage-progress':
                    self._storage_progress(value);continue
                if action=='progress':
                    self.bar['value']=value
                    if not self.cancel.is_set():self.phase.set('Verifying and preparing update…' if value>=100 else f'Downloading · {value:.0f}%')
                    continue
                finished_operation=self.operation;self.busy=False;self.operation=''
                if action in ('storage-clean','storage-auto'):
                    message=storage.summary(value)
                    if action=='storage-clean' or value['removedFiles'] or value['sharedBytes']:
                        self.status.set(message);self.preflight_text.configure(state='normal');self.preflight_text.delete('1.0','end');self.preflight_text.insert('1.0',message);self.preflight_text.configure(state='disabled')
                    self._sync();continue
                if action=='error' and finished_operation.startswith('storage-'):
                    self.cleanup_bar.stop();self.cleanup_eta.set('Cleanup could not complete: '+value)
                    self.status.set('Cleanup skipped: '+value);self._sync();continue
                if action=='tool-result' or action=='error' and finished_operation=='tool-result':
                    self.tool_text.configure(state='normal');self.tool_text.delete('1.0','end');self.tool_text.insert('1.0',value);self.tool_text.configure(state='disabled');self.status.set('Read-only inspection complete.' if action=='tool-result' else 'Inspection could not complete: '+value);self._sync();continue
                if action=='research-launch':self.status.set(value);self._sync();continue
                if action=='error' and finished_operation=='research-launch':self.status.set(value);self._sync();continue
                if action in ('lan-host','lan-join'):
                    self.connection_status.set(value);self.launch(action[4:]);self._sync();continue
                if action=='connection':
                    self.connection_status.set(value);self.status.set('Connection check complete.');self._sync();continue
                if action=='repair-feed':
                    self.repair_release=value;self.status.set('Published build available. Repair game files will download and verify it.');self._sync();continue
                if action=='integrity':
                    self.status.set(value);self.preflight_text.configure(state='normal');self.preflight_text.delete('1.0','end');self.preflight_text.insert('1.0',value);self.preflight_text.configure(state='disabled');self._sync();continue
                if action=='diagnostics':
                    self.status.set('Report prepared. Review before sharing.');self._review_report(Path(value));self._sync();continue
                if action=='feed':
                    self.news=value['news'];self._render_news()
                    self.news_status.set('Up to date · patch notes from GitHub' if value.get('newsSource')=='patchnotes' else 'Using release notes while patch notes are unavailable')
                    try:
                        cache=self.home/'.updates/news-cache.json'
                        prefs.atomic(cache,json.dumps(self.news))
                    except OSError:self.news_status.set('News refreshed · offline cache could not be saved')
                    latest=value.get('release')
                    if latest is None:
                        self.release=None;self.available.set('Update check unavailable')
                        self.status.set('Patch notes refreshed. Update information is unavailable right now.')
                        self.update_status.set('Your installed game is unchanged. Try checking for updates again later.')
                        self.nav['Updates'].configure(text='Updates');self._sync();continue
                    self.available.set('Release '+latest['version'])
                    if latest['numbers']>updates.installed_version(self.home):
                        self.release=latest;self.status.set('Release '+latest['version']+' is available in Updates.');self.update_status.set('A new Windows build is ready to install.');self.nav['Updates'].configure(text='Updates  •')
                    else:
                        self.release=None;self.status.set('You have the latest compatible release.');self.update_status.set('You’re up to date.');self.nav['Updates'].configure(text='Updates')
                elif action=='installed':
                    self.root=value;self.release=None;self.bar['value']=100;self.installed.set(self._version_text());self.footer_version.configure(text=self._version_text())
                    self.status.set('Update installed. Play uses the new build.');self.update_status.set('Verified and installed successfully.')
                    self.phase.set('Ready · Restarting launcher…');self.nav['Updates'].configure(text='Updates')
                    if not self.testing:self.after(350,self._restart_updated_launcher)
                else:
                    self.status.set(value+' Offline play remains available.');self.update_status.set(value);self.phase.set('Current build unchanged')
                    if finished_operation.startswith('lan-'):self.lan_status.set(value)
                    if finished_operation=='connection':
                        self.connection_status.set(value);self.status.set(value)
                    if finished_operation=='feed':self.news_status.set('Could not refresh · showing saved patch notes')
                self._sync()
        except queue.Empty:pass
        self._reap_game_workers();self._read_lan_status();self._sync();self.after(100,self._poll)

    def _read_lan_status(self):
        if not self.lan_request or time.monotonic()-self.lan_status_time<1:return
        self.lan_status_time=time.monotonic()
        if self.game is not None and self.game.poll() is not None:
            self.lan_status.set('Disconnected · game closed. Use Retry to reconnect.');self.lan_request='';return
        try:
            path=self.root/'builds/current/launcher-lan-status.json'
            if path.stat().st_size>8192:return
            if time.time()-path.stat().st_mtime>5:self.lan_status.set('Status unavailable · the game is not reporting.');return
            result=json.loads(path.read_text())
            if not isinstance(result,dict):return
            if result.get('request')!=self.lan_request:return
            if not result.get('ok'):self.lan_status.set(result.get('reason','LAN setup failed.'));return
            if result.get('role')==0:self.lan_status.set('LAN disconnected. Close the game to host or join again.');return
            players=result.get('players',[])
            if not isinstance(players,list) or not all(isinstance(p,dict) for p in players):return
            count=sum(p.get('status') in (1,2) for p in players)
            if count>=2:self.lan_was_connected=True
            elif self.lan_was_connected:self.lan_status.set('Disconnected · teammate left. Waiting for reconnect.');return
            self.lan_status.set('LAN connected · '+str(count)+' players' if count>=2 else 'LAN host ready · waiting for a friend' if result.get('role')==1 else 'LAN joining · waiting for host')
        except (OSError,ValueError,TypeError):
            if time.monotonic()-self.lan_started>30:self.lan_status.set('No LAN response. Save and close the game, then Retry.')

    def _retry_lan(self):
        if self._game_is_running():
            self.lan_status.set('Save and close the game before retrying.');return
        self._start_lan(self.last_lan_action)

    def _features_page(self,parent):
        self._heading(parent,'FEATURES','Features','Explore Mega Evolution, co-op and more')
        mega=card(parent);mega.pack(fill='x',pady=(0,12))
        art=tk.Frame(mega,bg=C['surface']);art.pack(anchor='w',padx=14,pady=(14,8))
        for side,filename in (('FRONT','mega-mawile-front.gif'),('BACK','mega-mawile-back.gif')):
            pose=tk.Frame(art,bg=C['surface']);pose.pack(side='left',padx=(0,18))
            label(pose,side,size=8,color=C['muted'],bg=C['surface']).pack(anchor='center')
            frames=[tk.PhotoImage(file=HERE/'assets/features'/filename,format=f'gif -index {frame}').zoom(2,2) for frame in range(72)]
            sprite=tk.Label(pose,image=frames[0],bg=C['surface'],bd=0);sprite.pack()
            self.feature_mega_frames.append(frames);self.feature_mega_labels.append(sprite)
        label(mega,'Mega Evolution',size=15,bold=True,bg=C['surface']).pack(anchor='w',padx=14)
        label(mega,'Try 49 Mega forms, each with its own matching Mega Stone. Give the stone to its Pokémon, then press L + R together while choosing a move in battle. Mega Evolution lasts until the battle ends.',size=10,color=C['muted'],bg=C['surface'],wraplength=570,justify='left').pack(anchor='w',padx=14,pady=(6,8))
        label(mega,'Examples: Mega Serperior gains Adaptability; Mega Charizard Y gains Drought; Mega Salamence gains Intimidate. Animated battle artwork is available for 46 forms.',size=10,bg=C['surface'],wraplength=570,justify='left').pack(anchor='w',padx=14,pady=(0,4))
        label(mega,'The launcher shows Mawile’s supplied front and back animation.',size=9,color=C['muted'],bg=C['surface']).pack(anchor='w',padx=14,pady=(2,0))
        button(mega,'Mega Evolution guide',lambda:self.guide('MEGA_EVOLUTION.md')).pack(anchor='w',padx=14,pady=(8,14))
        story=card(parent);story.pack(fill='x',pady=(0,12))
        label(story,'Cynthia’s Route 7 challenge',size=13,bold=True,bg=C['surface']).pack(anchor='w',padx=14,pady=(14,4))
        label(story,'After you defeat Skyla, Cynthia appears near the Mistralton City and Route 7 transition. She explains Mega Evolution and gives you a stone for a Pokémon in your party, or a Serperiorite if no one is ready. Return later to challenge her team and Mega Garchomp. For Blaze Black 2 Redux Complete v1.4.1, the launcher prepares a separate event-ready copy and keeps your selected game file and saves intact.',size=10,color=C['muted'],bg=C['surface'],wraplength=570,justify='left').pack(anchor='w',padx=14,pady=(4,14))
        companion=card(parent);companion.pack(fill='x',pady=(0,12))
        label(companion,'Companion interactions',size=13,bold=True,bg=C['surface']).pack(anchor='w',padx=14,pady=(14,4))
        label(companion,'Expanded in 1.0.6 · on by default in this launcher',size=9,color=C['muted'],bg=C['surface']).pack(anchor='w',padx=14)
        for copy in (
            'Talk, pet, play, praise, tell a story, ask about today, sit together, show a trick, tell a joke or sing together.',
            'Five friendship bands, subtle nature cues and session visit counts. Area, calendar, Pokémon type and recent battles add context. Hearts, !, ?, stars and notes accompany peeks, sways, hops, spins and short runs.',
            'Stop, face your follower and press R+A, or tap its sprite. A alone advances game text. Manage interactions in Settings → Following Pokémon; show or hide followers in Unova → Settings.',
            'Cosmetic only: HP, friendship, items and saves are unchanged.'):
            text=label(companion,copy,size=10,bg=C['surface'],wraplength=570,justify='left')
            text.pack(anchor='w',padx=14,pady=(8,4))
            companion.bind('<Configure>',lambda e,w=text:w.configure(wraplength=max(240,e.width-32)),add='+')
        button(companion,'Interaction guide',lambda:self.guide('COMPANION_INTERACTIONS.md')).pack(anchor='w',padx=14,pady=(8,14))
        entries=(
            ('walking','Explore together','See teammates and their followers on the map. Unova → Players shows their status and offers Join map / Teleport.'),
            ('items','Give items','Send an item and quantity from Unova → Players. Your teammate accepts the offer; both players save afterward.'),
            ('battle','Co-op trainer battles','Choose Solo or Co-op before an encounter. Supported trainers and practice rematches use independent parties and saves. Co-op XP is disabled; interrupted battles may roll back.'),
            ('pokemon','Pokémon trades & player battles','Exchange party Pokémon or request a friendly battle from Unova → Players. Direct trades exclude eggs, held Mail and trade evolutions.'),
            ('camera','Custom camera','Adjust tilt, rotation and zoom in System → Multiplayer → Camera. Each player chooses their own view.'),
            ('stats','Party IVs & EVs','Open Unova → Pokémon → IVs and EVs to view each Pokémon’s stats.'))
        for asset,title,description in entries:
            panel=card(parent);panel.pack(fill='x',pady=(0,12))
            image=tk.PhotoImage(file=HERE/f'assets/features/{asset}.png');self.images.append(image)
            tk.Label(panel,image=image,bg=C['surface'],bd=0).pack(anchor='w',padx=14,pady=(14,8))
            label(panel,title,size=13,bold=True,bg=C['surface']).pack(anchor='w',padx=14)
            text=label(panel,description,size=10,color=C['muted'],bg=C['surface'],wraplength=570,justify='left');text.pack(anchor='w',padx=14,pady=(6,14))
            panel.bind('<Configure>',lambda e,w=text:w.configure(wraplength=max(240,e.width-32)))
        extras=card(parent);extras.pack(fill='x')
        for title,copy in (
            ('Following Pokémon','649 base species plus supported female and form variants: 743 directional assets with normal and shiny palettes. Larger art retains its original dimensions. Unsupported forms use base art. Reduced follower motion is available in Settings.'),
            ('Super Repels','Super Repels cost ₽10, the lowest positive price supported by the game. Available in active ordinary money shops. ROM files and saves are not edited.'),
            ('Encounter finder & move relearning','Unova → Pokémon lists ordinary wild encounters by season and offers free level-up move relearning. Gifts, scripted legendaries and Hidden Grottos are excluded.'),
            ('Field HMs','Owned HMs work without occupying battle move slots. Native story requirements still apply; Fly needs an available field-action slot.'),
            ('Solo XP','Supported solo battles award 1.25× XP automatically. Existing XP is unchanged. Co-op battles award no XP.'),
            ('Area battle scenery · optional','Generate nearby battle scenery locally from your ROM. Enable Nearby battle scenery in Settings. This remains experimental; special scenes keep original backgrounds, and environments are not all playtested.'),
            ('LAN & internet play','Host, join and retry from Co-op. Use Tailscale across networks. The UDP bridge is experimental and needs your group’s server and Python; no public server is supplied.'),
            ('Games & saves','Separate save slots, automatic names and per-slot settings. Back up and restore saves from Games & saves or Tools; old installations can be cleaned while keeping saves and backups.'),
            ('Player appearance','Choose an animated character model stored in your supported game. It changes your walking character; bike and surf forms keep their original animations.'),
            ('Generation 5 menu sounds','The added in-game menus use movement, confirmation and back sounds inspired by Generation 5 games. Turn them off from the in-game Unova → Settings menu.'),
            ('Gen 5 tools','Check ROM compatibility, compare copied saves and estimate Redux Challenge XP budgets. These tools read data; they do not edit your game.'),
            ('Settings & maintenance','Controller navigation, music, emulator settings and reviewed optional cheats. Verified updates, repair and reviewed troubleshooting reports are available.')):
            label(extras,title,size=12,bold=True,bg=C['surface']).pack(anchor='w',padx=14,pady=(12,4))
            text=label(extras,copy,size=10,color=C['muted'],bg=C['surface'],wraplength=570,justify='left');text.pack(anchor='w',padx=14,pady=(0,8))
            extras.bind('<Configure>',lambda e,w=text:w.configure(wraplength=max(240,e.width-32)),add='+')
        guides=tk.Frame(parent,bg=C['background']);guides.pack(fill='x',pady=12)
        for title,doc in (('Feature guide','FEATURES.md'),('Known issues','KNOWN_ISSUES.md'),('Roadmap','ROADMAP.md')):
            button(guides,title,lambda name=doc:self.guide(name)).pack(side='left',padx=(0,8))

    def _set_feature_mega_animation(self,active):
        if active:
            if self.feature_mega_after is None and self.feature_mega_frames:
                self.feature_mega_after=self.after(80,self._advance_feature_mega_animation)
        elif self.feature_mega_after is not None:
            self.after_cancel(self.feature_mega_after);self.feature_mega_after=None

    def _advance_feature_mega_animation(self):
        self.feature_mega_after=None
        if not self.feature_mega_frames:return
        self.feature_mega_frame=(self.feature_mega_frame+1)%len(self.feature_mega_frames[0])
        for widget,frames in zip(self.feature_mega_labels,self.feature_mega_frames):
            widget.configure(image=frames[self.feature_mega_frame])
        if self.page_name=='Features':self.feature_mega_after=self.after(80,self._advance_feature_mega_animation)

    def _cycle_page(self,direction):
        names=list(self.visible_pages);self.show_page(names[(names.index(self.page_name)+direction)%len(names)]);self.nav[self.page_name].focus_set();return 'break'

    def _controller_action(self,action):
        focused=self.focus_get()
        if action=='next':self._cycle_page(1)
        elif action=='previous':self._cycle_page(-1)
        elif action=='back':
            if focused and focused.winfo_toplevel()!=self:focused.winfo_toplevel().destroy()
            else:
                first=game_routes.MODS[self.active_mod]['pages'][0] if self.active_mod else 'Library'
                if self.page_name==first:self._return_library()
                else:self.show_page(first);self.nav[first].focus_set()
        elif action in ('up','down'):
            widget=focused or self.nav[self.page_name]
            target=widget.tk_focusPrev() if action=='up' else widget.tk_focusNext()
            if target:target.focus_set()
        elif action in ('left','right') and isinstance(focused,ttk.Combobox):
            values=focused['values'];index=focused.current()
            if values:focused.current((index+(-1 if action=='left' else 1))%len(values));focused.event_generate('<<ComboboxSelected>>')
        elif action in ('left','right') and isinstance(focused,tk.Scale):focused.set(focused.get()+(-5 if action=='left' else 5))
        elif action=='accept' and focused:
            if hasattr(focused,'invoke'):focused.invoke()
            elif isinstance(focused,ttk.Combobox):focused.event_generate('<Alt-Down>')

    def _poll_controller(self):
        active=False
        if not self.testing and os.name=='nt':
            import ctypes
            focused=self.focus_get()
            if focused:
                user32=ctypes.windll.user32
                user32.GetForegroundWindow.restype=ctypes.c_void_p
                user32.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint];user32.GetAncestor.restype=ctypes.c_void_p
                active=user32.GetForegroundWindow()==user32.GetAncestor(focused.winfo_toplevel().winfo_id(),2)
        for action in sorted(self.controller.poll(active)):self._controller_action(action)
        self.after(125,self._poll_controller)

    def _toggle_music(self):
        self.music.set(not self.music.get());self._music_changed()

    def _music_changed(self,save=True):
        self.music_button.configure(text='Music: on' if self.music.get() else 'Music: off')
        self._stop_music()
        if self.music.get() and not self.testing and (self.game is None or self.game.poll() is not None):
            try:
                import winsound
                winsound.PlaySound(str(HERE/'assets/menu-music.wav'),winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_LOOP|winsound.SND_NODEFAULT)
            except (ImportError,RuntimeError,OSError):
                self.music.set(False);self.music_button.configure(text='Music: off');self.status.set('Music unavailable.')
        if save:self._save()

    def _stop_music(self):
        if self.testing:return
        try:
            import winsound
            winsound.PlaySound(None,0)
        except (ImportError,RuntimeError):pass

    def _restart_updated_launcher(self):
        # Restart the installed launcher, preserving the persistent profile/save home.
        try:
            executable=versioning.restart_executable(self.root)
            if not executable.is_file():raise OSError('Updated launcher executable is missing.')
            self._save()
            try:launcher_migration.schedule(self.home,self.root)
            except (OSError,ValueError):pass
            env=dict(os.environ)
            # A frozen parent must not lend its temporary PyInstaller runtime to the child.
            env['PYINSTALLER_RESET_ENVIRONMENT']='1'
            subprocess.Popen([str(executable),'--home',str(self.home)],cwd=self.root,env=env)
        except (OSError,ValueError) as exc:
            self.status.set('Update installed. Could not restart the launcher.')
            self.update_status.set(str(exc));self.phase.set('Ready · Close and reopen the launcher.')
            return
        self.destroy()

    def _close(self):
        if self.busy and not messagebox.askyesno('Cancel update?','Close the launcher and cancel the current check/download?',parent=self):return
        self.cancel.set();self._save();self.destroy()

    def destroy(self):
        # Cancel this Tcl interpreter's UI timers before disposing its widgets.
        self.cancel.set();self._stop_music();self._stop_game_workers()
        for token in self.tk.call('after','info'):self.after_cancel(token)
        super().destroy()
