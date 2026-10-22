"""Native launcher UI by mvq1303 / WhatWasMissing. Updater owns installation."""
from pathlib import Path
import hashlib, json, os, queue, random, re, time, uuid, subprocess, sys, threading, tkinter as tk, webbrowser, zipfile
import tomlkit
from tkinter import filedialog, messagebox, ttk
import unova_updater as updates
import unova_storage as storage
import launcher_migration
from PIL import Image, ImageTk
from . import preferences as prefs
from . import services
from . import gen5_tools
from . import player_models
from . import player_model_preferences as model_preferences
from . import cynthia_event
from . import game_routes
from . import versioning
from .components import C, F, HERE, THEME, ScrollPage, button, card, emblem, label, set_enabled

class Launcher(tk.Tk):
    def __init__(self,home,testing=False):
        super().__init__()
        self.home=Path(home).resolve();self.root=updates.active_root(self.home,allow_missing=True);self.testing=testing
        self.config_path=self.home/'.launcher-test.json' if testing else Path(os.environ.get('APPDATA',Path.home()))/'UnovaTogether/launcher.json'
        self.title('Pokemon Together');self.geometry('1040x760');self.minsize(THEME['layout']['minWidth'],THEME['layout']['minHeight']);self.configure(bg=C['background'])
        try:self.iconbitmap(str(HERE/'assets/launcher.ico'))
        except tk.TclError:pass
        self.messages=queue.Queue();self.busy=False;self.release=None;self.game=None;self.operation='';self.guides_busy=False
        self._process_check_at=0;self._process_running=False
        self.cancel=threading.Event();self.rom=tk.StringVar();self.auto=tk.BooleanVar(value=True);self.music=tk.BooleanVar(value=False)
        self.status=tk.StringVar(value='');self.news_status=tk.StringVar(value='Saved patch notes · available offline')
        self.update_status=tk.StringVar(value='Check GitHub for the latest Windows release.')
        self.available=tk.StringVar(value='Not checked yet');self.phase=tk.StringVar(value='No download in progress')
        self.news=self._read_news();self.pages={};self.nav={};self.images=[];self.page_name=''
        self.feature_mega_frames=[];self.feature_mega_photos=[];self.feature_mega_static=[];self.feature_mega_labels=[];self.feature_mega_frame=0;self.feature_mega_after=None
        self.feature_mega_loading=False;self.feature_mega_loaded=False
        self.feature_gen5_art=[]
        self.play_fan_art=[]
        self.preference_values={};self.cheat_choices={};self.profile=None;self.rom_timer=None;self.tailscale_guide_ack=''
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
        style.configure('TScrollbar',background=C['border'],troughcolor=C['background'],arrowcolor=C['muted'],borderwidth=0,arrowsize=13)
        style.map('TScrollbar',background=[('active',C['muted'])])
        style.configure('TProgressbar',background=C['primary'],troughcolor=C['selection'],borderwidth=0,thickness=9)
        style.configure('TCheckbutton',background=C['surface'],foreground=C['text'],font=(F['body'],11),padding=(3,5))
        style.map('TCheckbutton',background=[('active',C['surface'])],foreground=[('disabled',C['disabledText'])])
        style.configure('TCombobox',fieldbackground=C['surface'],background=C['surface'],foreground=C['text'],arrowcolor=C['primary'],bordercolor=C['border'],lightcolor=C['border'],darkcolor=C['border'],padding=7)
        style.map('TCombobox',fieldbackground=[('readonly',C['surface']),('disabled',C['disabled'])],foreground=[('readonly',C['text']),('disabled',C['disabledText'])])
        style.configure('TEntry',fieldbackground=C['surface'],foreground=C['text'],padding=7)
        style.map('TEntry',fieldbackground=[('disabled',C['disabled'])],foreground=[('disabled',C['disabledText'])])
        self.nav_cursor=tk.PhotoImage(file=HERE/'assets/menu-cursor.png');self.images.append(self.nav_cursor)
        sidebar=tk.Frame(self,bg=C['nav'],width=THEME['layout']['sidebar']);self.sidebar=sidebar;sidebar.pack(side='left',fill='y');sidebar.pack_propagate(False)
        emblem(sidebar,size=42).pack(anchor='w',padx=22,pady=(10,4))
        label(sidebar,'POKEMON\nTOGETHER',size=16,bold=True,color=C['surface'],bg=C['nav'],role='display',justify='left').pack(anchor='w',padx=22)
        self.mod_caption=label(sidebar,'MULTIPLAYER MODS',size=9,bold=True,color=C['navText'],bg=C['nav'],wraplength=170)
        self.mod_caption.pack(anchor='w',padx=22,pady=(5,4))
        self.nav_sections={name:label(sidebar,name,size=8,bold=True,color=C['navText'],bg=C['nav'],role='utility') for name in ('MOD LIBRARY','PLAY','MANAGE','EXPERIMENTAL')}
        for name in ('Library','Play','Co-op','Features','Profiles','News','Updates','Settings','Tools','Setup','XPlay','XCoop','XGuides'):
            self.nav[name]=button(sidebar,game_routes.PAGE_LABELS.get(name,name),lambda n=name:self.show_page(n),kind='nav',anchor='w')
        credit=tk.Frame(sidebar,bg=C['nav']);credit.pack(side='bottom',fill='x',padx=20,pady=4)
        label(credit,'Made by mvq1303',size=10,color=C['surface'],bg=C['nav']).pack(anchor='w')
        label(credit,'WhatWasMissing\nBuilt on melonDS / Azahar',size=9,color=C['navText'],bg=C['nav'],justify='left').pack(anchor='w',pady=(5,0))
        shell=tk.Frame(self,bg=C['background']);shell.pack(side='right',fill='both',expand=True)
        footer=tk.Frame(shell,bg=C['surface'],height=48,highlightbackground=C['border'],highlightthickness=1);footer.pack(side='bottom',fill='x');footer.pack_propagate(False)
        self.music_button=button(footer,'Music: off',self._toggle_music);self.music_button.pack(side='right',padx=4)
        self.footer_version=label(footer,self._version_text(),size=9,color=C['muted'],bg=C['surface'],role='utility');self.footer_version.pack(side='right',padx=18)
        self.footer_status=label(footer,size=10,bg=C['surface'],textvariable=self.status);self.footer_status.pack(side='left',fill='x',expand=True,padx=18)
        self.footer_activity=ttk.Progressbar(footer,mode='indeterminate',length=58)
        self._activity_running=False
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
        self.bind('<Configure>',self._responsive_layout,add='+')

    def _responsive_layout(self,event):
        if event.widget is not self:return
        compact=event.width<980
        if getattr(self,'_compact_layout',None)==compact:return
        self._compact_layout=compact
        layout=THEME['layout']
        self.sidebar.configure(width=layout['sidebarCompact'] if compact else layout['sidebar'])
        padding=layout['paddingCompact'] if compact else layout['padding']
        self.deck.pack_configure(padx=padding,pady=padding)

    def _heading(self,parent,kicker,title,subtitle):
        if kicker:label(parent,kicker.upper(),size=9,bold=True,color=C['primary'],role='utility').pack(anchor='w',pady=(0,5))
        label(parent,title,size=25,bold=True,role='display').pack(anchor='w',pady=(0,0 if subtitle else 14))
        if subtitle:
            note=label(parent,subtitle,size=10,color=C['muted'],wraplength=700,justify='left')
            note.pack(anchor='w',pady=(5,16))
            parent.bind('<Configure>',lambda e,w=note:w.configure(wraplength=max(260,e.width-12)),add='+')

    def _load_gif_frames(self,path,scale=1):
        frames=[]
        with Image.open(path) as animation:
            for index in range(getattr(animation,'n_frames',1)):
                animation.seek(index);frame=animation.convert('RGBA')
                if scale!=1:
                    width,height=frame.size
                    frame=frame.resize((width*scale,height*scale),Image.Resampling.NEAREST)
                frames.append(frame.copy())
        return frames

    def _load_feature_mega_worker(self):
        try:
            assets=HERE/'assets/features'
            frames=[self._load_gif_frames(assets/name,scale=2) for name in ('mega-mawile-front.gif','mega-mawile-back.gif')]
            self.messages.put(('feature-mega-frames',frames))
        except Exception as exc:
            self.messages.put(('feature-mega-error',str(exc)))

    def _ensure_feature_mega_loaded(self):
        if self.feature_mega_loading or self.feature_mega_loaded:return
        self.feature_mega_loading=True;self.feature_art_status.configure(text='Loading animated sprite previews…')
        threading.Thread(target=self._load_feature_mega_worker,daemon=True).start()

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
        art=tk.Frame(hero,bg=C['hero']);art.pack(side='right',padx=(0,18),pady=18)
        label(art,'MEGA ALTARIA · GEN 5 STYLE',size=8,bold=True,color=C['accent'],bg=C['hero']).pack(anchor='center',pady=(0,2))
        art_sprites=tk.Frame(art,bg=C['hero']);art_sprites.pack()
        for filename in ('mega-altaria-front.gif','mega-altaria-back.gif'):
            picture=tk.PhotoImage(file=HERE/'assets/features/gen5-fan'/filename,format='gif -index 0')
            self.images.append(picture);self.play_fan_art.append(picture)
            tk.Label(art_sprites,image=picture,bg=C['hero'],bd=0).pack(side='left',padx=2)
        words=tk.Frame(hero,bg=C['hero']);words.pack(side='left',fill='both',expand=True,padx=24,pady=24)
        label(words,'BLAZE BLACK 2 REDUX · CO-OP',size=9,bold=True,color=C['accent'],bg=C['hero']).pack(anchor='w')
        label(words,'Pokemon\nTogether',size=25,bold=True,color=C['surface'],bg=C['hero'],role='display',justify='left').pack(anchor='w',pady=(10,12))
        label(words,'Mega Evolution · co-op · animated followers',size=10,color=C['accent'],bg=C['hero']).pack(anchor='w')
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
        if name=='Features':self._ensure_feature_mega_loaded()
        self._set_feature_mega_animation(name=='Features')
        context=game_routes.MODS[self.active_mod]['name']+' · ' if self.active_mod and name!='Library' else ''
        self.title('Pokemon Together · '+context+game_routes.PAGE_LABELS.get(name,name))
        if isinstance(self.pages[name],ScrollPage):self.pages[name].canvas.yview_moveto(0)
        self._highlight_navigation(name)

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
        label(third,'Host & play starts a LAN lobby. Your friend uses Join & play. Turn C-Gear wireless and fast-forward off. For cross-network Tailscale play, the launcher requires you to scroll through and acknowledge the setup guide first.',size=10,color=C['muted'],bg=C['surface'],wraplength=590,justify='left').pack(anchor='w',padx=18,pady=(0,8))
        label(third,'Alternatives: use Local LAN on the same network, ZeroTier with manual firewall setup, or the experimental UDP relay hosted by your group.',size=10,color=C['muted'],bg=C['surface'],wraplength=590,justify='left').pack(anchor='w',padx=18,pady=(0,14))
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
        self.mode_help.set({'Local LAN':'For computers on the same home network.','Tailscale backup':'Tailscale for different networks. Read the full setup before hosting or joining.','Internet UDP':'Experimental. Needs a server hosted by your group.','Solo':'Multiplayer off.'}.get(mode,''))
        self.mode_action.configure(text='Open internet setup' if mode=='Internet UDP' else 'Read Tailscale setup' if mode=='Tailscale backup' else 'Open play guide')

    def _connection_guide(self):
        if self.net_mode.get()=='Internet UDP':self._internet_wizard()
        else:self.guide('TAILSCALE_COOP.md' if self.net_mode.get()=='Tailscale backup' else 'PLAYER_GUIDE.md')

    def _tailscale_guide_content(self):
        guide=self.root/'docs'/'TAILSCALE_COOP.md'
        if not guide.is_file():guide=services.cached_guide(self.home,'TAILSCALE_COOP.md')
        if not guide or not guide.is_file():raise OSError('The Tailscale setup guide is unavailable. Repair or update Unova Together, then try again.')
        data=guide.read_bytes()
        if not data or len(data)>131072:raise ValueError('The Tailscale setup guide is invalid or too large.')
        return data.decode('utf-8'),hashlib.sha256(data).hexdigest()

    def _require_tailscale_guide_review(self):
        try:content,digest=self._tailscale_guide_content()
        except (OSError,ValueError,UnicodeError) as exc:
            self.lan_status.set(str(exc));return False
        if self.tailscale_guide_ack==digest:return True
        if not self._show_tailscale_guide_review(content):
            self.lan_status.set('Read and acknowledge the Tailscale setup before starting a cross-network session.');return False
        self.tailscale_guide_ack=digest;self._save()
        return True

    def _show_tailscale_guide_review(self,content):
        window=tk.Toplevel(self);window.title('Tailscale setup · read before connecting');window.geometry('760x660');window.minsize(620,500);window.transient(self)
        label(window,'Before you connect across networks',size=18,bold=True).pack(anchor='w',padx=18,pady=(16,4))
        label(window,'Review the complete setup below. Host and guest must use the same Tailscale network, game version, release and room.',size=10,color=C['muted'],wraplength=710,justify='left').pack(anchor='w',padx=18,pady=(0,10))
        body=tk.Frame(window,bg=C['surface']);body.pack(fill='both',expand=True,padx=18)
        scroll=ttk.Scrollbar(body,orient='vertical');scroll.pack(side='right',fill='y')
        text=tk.Text(body,wrap='word',font=(F['body'],10),bg=C['surface'],fg=C['text'],relief='flat',padx=12,pady=10,spacing1=2,spacing3=5,yscrollcommand=scroll.set)
        text.pack(side='left',fill='both',expand=True);scroll.configure(command=text.yview)
        def plain_markdown(source):
            lines=[]
            for line in source.splitlines():
                line=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 — \2',line)
                line=re.sub(r'^#{1,6}\s*','',line)
                line=re.sub(r'^\s*[-*]\s+','• ',line)
                lines.append(line.replace('**','').replace('`',''))
            return '\n'.join(lines)
        text.insert('1.0',plain_markdown(content));text.configure(state='disabled')
        actions=tk.Frame(window,bg=C['background']);actions.pack(fill='x',padx=18,pady=(10,16))
        reviewed=tk.BooleanVar(value=False);reached_end={'value':False};accepted={'value':False}
        check=ttk.Checkbutton(actions,text='I have read the setup and checked that my group can follow these steps.',variable=reviewed,state='disabled')
        check.pack(anchor='w',pady=(0,10))
        controls=tk.Frame(actions,bg=C['background']);controls.pack(fill='x')
        button(controls,'Open Tailscale Windows instructions',lambda:webbrowser.open('https://tailscale.com/docs/install/windows')).pack(side='left')
        continue_button=button(controls,'Continue',lambda:None,kind='primary');continue_button.pack(side='right')
        button(controls,'Cancel',window.destroy).pack(side='right',padx=(0,8))
        set_enabled(continue_button,False)
        def update_continue(*_):set_enabled(continue_button,reached_end['value'] and reviewed.get(),'primary')
        reviewed.trace_add('write',update_continue)
        def update_read_progress(*_):
            first,last=map(float,text.yview());scroll.set(first,last)
            if last>=0.999:
                reached_end['value']=True;check.state(['!disabled'])
            update_continue()
        def scroll_text(*args):
            text.yview(*args);update_read_progress()
        def on_scroll(first,last):
            scroll.set(first,last);update_read_progress()
        def schedule_read_progress(_event=None):window.after_idle(update_read_progress)
        scroll.configure(command=scroll_text)
        for sequence in ('<MouseWheel>','<Button-4>','<Button-5>'):
            text.bind(sequence,schedule_read_progress,'+')
        def accept():
            if reached_end['value'] and reviewed.get():accepted['value']=True;window.destroy()
        continue_button.configure(command=accept)
        text.configure(yscrollcommand=on_scroll)
        window.protocol('WM_DELETE_WINDOW',window.destroy);window.grab_set();window.focus_force();window.wait_window()
        return accepted['value']

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
        self.settings_sections={}
        shortcuts=tk.Frame(parent,bg=C['background']);shortcuts.pack(fill='x',pady=(0,14))
        self.settings_jumps={}
        for title,section in (('General','General'),('Co-op','Co-op'),('Followers','Followers'),('Appearance','Appearance'),('Cheats','Cheats')):
            control=button(shortcuts,title,lambda key=section:self._jump_settings(key))
            control.pack(side='left',fill='x',expand=True,padx=(0,6))
            self.settings_jumps[section]=control
        general=card(parent);general.pack(fill='x',pady=(0,18))
        self.settings_sections['General']=general
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
        self.settings_sections['Co-op']=coop_test
        coop_test_box=tk.Frame(coop_test,bg=C['surface']);coop_test_box.pack(fill='x',padx=18,pady=16)
        label(coop_test_box,'CO-OP TESTING',size=9,bold=True,bg=C['surface']).pack(anchor='w',pady=(0,8))
        self.coop_exp_suppression=tk.BooleanVar(value=values.get('coop_exp_suppression',True))
        ttk.Checkbutton(coop_test_box,text='Suppress EXP in co-op battles (testing)',variable=self.coop_exp_suppression,
            command=lambda:self._preference('coop_exp_suppression',self.coop_exp_suppression.get())).pack(anchor='w',pady=4)
        label(coop_test_box,'Skips EXP, level-up and move-learning rewards during co-op test/story battles. On by default; turn it off to test normal EXP rewards. Applies on the next launch.',size=9,color=C['muted'],bg=C['surface'],wraplength=620,justify='left').pack(anchor='w',pady=(2,0))
        followers=card(parent);followers.pack(fill='x',pady=(0,18))
        self.settings_sections['Followers']=followers
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
        self.settings_sections['Appearance']=appearance
        appearance_box=tk.Frame(appearance,bg=C['surface']);appearance_box.pack(fill='x',padx=18,pady=16)
        label(appearance_box,'PLAYER APPEARANCE',size=9,bold=True,bg=C['surface']).pack(anchor='w')
        self.player_model_label=tk.StringVar()
        self._refresh_player_model_label()
        label(appearance_box,textvariable=self.player_model_label,size=11,bold=True,bg=C['surface']).pack(anchor='w',pady=(8,4))
        button(appearance_box,'Choose a field character',self._choose_player_model).pack(anchor='w',pady=(6,8))
        label(appearance_box,'Browse and preview animated people and Pokémon from your game. Filter or search the list, keep favorites, save named looks, or choose at random. Battle portraits are separate art. Only normal walking changes; bike and surf keep their original forms. Applies next launch.',size=9,color=C['muted'],bg=C['surface'],wraplength=620,justify='left').pack(anchor='w')
        cheats=card(parent);cheats.pack(fill='x')
        self.settings_sections['Cheats']=cheats
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

    def _jump_settings(self,section):
        target=self.settings_sections.get(section)
        page=self.pages.get('Settings')
        if target is None or not isinstance(page,ScrollPage):return
        page.canvas.update_idletasks()
        height=max(1,page.content.winfo_height())
        page.canvas.yview_moveto(min(1,max(0,target.winfo_y()/height)))

    def _preference(self,key,value):
        self.preference_values[key]=value;self._save()

    def _refresh_player_model_label(self):
        model_id=self.preference_values.get('player_model',0)
        self.player_model_label.set('Default character' if model_id==0 else player_models.display_name(model_id))

    def _choose_player_model(self):
        source=Path(self.rom.get())
        if not source.is_file() or source.suffix.lower()!='.nds':
            self.status.set('Choose a supported Redux game on Play before selecting a character.');return
        window=tk.Toplevel(self);window.title('Choose field character');window.geometry('720x650');window.minsize(560,500);window.transient(self)
        outer=tk.Frame(window,bg=C['background']);outer.pack(fill='both',expand=True,padx=16,pady=16)
        label(outer,'Choose your field character',size=16,bold=True,bg=C['background']).pack(anchor='w')
        label(outer,'Browse animated people and Pokémon from the selected game. Preview graphics are read from your ROM.',size=9,color=C['muted'],bg=C['background'],wraplength=660,justify='left').pack(anchor='w',pady=(6,12))
        query=tk.StringVar();entry=tk.Entry(outer,textvariable=query,font=(F['body'],11),highlightthickness=2,highlightcolor=C['focus']);entry.pack(fill='x',pady=(0,8))
        browse=tk.Frame(outer,bg=C['background']);browse.pack(fill='x',pady=(0,8))
        category=tk.StringVar(value=model_preferences.FILTER_ALL);category_box=ttk.Combobox(browse,textvariable=category,state='readonly',values=model_preferences.FILTERS,width=18);category_box.pack(side='left')
        sort=tk.StringVar(value='Alphabetical');sort_box=ttk.Combobox(browse,textvariable=sort,state='readonly',values=('Alphabetical','Model number'),width=16);sort_box.pack(side='left',padx=(8,0))
        body=tk.Frame(outer,bg=C['background']);body.pack(fill='both',expand=True)
        body.columnconfigure(0,weight=3);body.columnconfigure(1,weight=2);body.rowconfigure(0,weight=1)
        list_card=tk.Frame(body,bg=C['surface']);list_card.grid(row=0,column=0,sticky='nsew',padx=(0,8))
        choices=tk.Listbox(list_card,font=(F['body'],10),bg=C['surface'],fg=C['text'],selectbackground=C['primary'],selectforeground=C['surface'],activestyle='none',exportselection=False,relief='flat',highlightthickness=0)
        scroll=ttk.Scrollbar(list_card,command=choices.yview);scroll.pack(side='right',fill='y');choices.configure(yscrollcommand=scroll.set);choices.pack(fill='both',expand=True,padx=(10,0),pady=10)
        preview_box=tk.Frame(body,bg=C['surface']);preview_box.grid(row=0,column=1,sticky='nsew')
        label(preview_box,'LIVE FIELD PREVIEW',size=9,bold=True,bg=C['surface']).pack(anchor='w',padx=12,pady=(12,4))
        preview=tk.Label(preview_box,text='Select a character to preview',font=(F['body'],9),bg=C['background'],fg=C['muted'],width=20,height=12,compound='center')
        preview.pack(fill='both',expand=True,padx=12,pady=8)
        preview_name=tk.StringVar(value='No character selected');label(preview_box,textvariable=preview_name,size=10,bold=True,bg=C['surface'],wraplength=205,justify='center').pack(fill='x',padx=8,pady=(0,4))
        preview_type=tk.StringVar(value='');label(preview_box,textvariable=preview_type,size=9,color=C['muted'],bg=C['surface'],wraplength=205,justify='center').pack(fill='x',padx=8,pady=(0,12))
        state=label(outer,'Reading character models…',size=9,color=C['muted'],bg=C['background']);state.pack(anchor='w',pady=(8,4))
        preset_row=tk.Frame(outer,bg=C['background']);preset_row.pack(fill='x',pady=(6,0))
        preset_name=tk.StringVar();preset_entry=tk.Entry(preset_row,textvariable=preset_name,font=(F['body'],10),highlightthickness=1,highlightcolor=C['focus'])
        preset_entry.pack(side='left',fill='x',expand=True)
        presets=tk.StringVar();preset_box=ttk.Combobox(preset_row,textvariable=presets,state='readonly',width=21);preset_box.pack(side='left',padx=(8,0))
        result_queue=queue.Queue();models=[];visible=[];ready=False;preview_generation=0;preview_timer=None;preview_playback=None;queue_poll=None;active_frames=[]
        selected_model=self.preference_values.get('player_model',0)
        def load_models():
            try:result_queue.put(('models',player_models.list_models(source)))
            except Exception as exc:result_queue.put(('error',str(exc)))
        threading.Thread(target=load_models,daemon=True).start()
        def populate(*_):
            nonlocal visible
            term=query.get().strip().casefold();current=choices.curselection();selected=visible[current[0]] if current else None
            visible=model_preferences.filter_models(models,term,category.get(),self.preference_values.get('player_model_favorites',[]),'number' if sort.get()=='Model number' else 'name')
            choices.delete(0,'end')
            favorites=set(self.preference_values.get('player_model_favorites',[]))
            for model in visible:choices.insert('end',('★ ' if model in favorites else '')+player_models.display_name(model))
            target=selected if selected in visible else selected_model if selected_model in visible else None
            if target is not None:
                index=visible.index(target);choices.selection_set(index);choices.see(index)
            update_favorite_label()
            refresh_presets()
        def current_choice():
            selected=choices.curselection()
            return visible[selected[0]] if selected and selected[0]<len(visible) else None
        def update_favorite_label():
            model=current_choice()
            favorite_button.configure(text='Remove favorite' if model in self.preference_values.get('player_model_favorites',[]) else 'Add favorite')
        def set_preview_message(message):
            nonlocal active_frames
            active_frames=[];preview.configure(image='',text=message);preview.image=None;preview_type.set('')
            if preview_playback is not None:
                try:window.after_cancel(preview_playback)
                except tk.TclError:pass
        def cancel_picker_jobs():
            nonlocal preview_generation,preview_timer,preview_playback,queue_poll
            preview_generation+=1
            for job in (preview_timer,preview_playback,queue_poll):
                if job is not None:
                    try:window.after_cancel(job)
                    except tk.TclError:pass
            preview_timer=preview_playback=queue_poll=None
        def close_picker():
            cancel_picker_jobs()
            try:window.destroy()
            except tk.TclError:pass
        def play_preview(frame_index=0):
            nonlocal preview_playback
            if not window.winfo_exists() or not active_frames:return
            image,duration=active_frames[frame_index]
            from PIL import Image,ImageTk
            image=ImageTk.PhotoImage(image.resize((128,128),resample=Image.Resampling.NEAREST))
            preview.configure(image=image,text='');preview.image=image
            preview_playback=window.after(duration,lambda:play_preview((frame_index+1)%len(active_frames)))
        def request_preview(*_):
            nonlocal preview_generation,preview_timer
            model=current_choice();preview_generation+=1;generation=preview_generation
            if preview_timer is not None:
                try:window.after_cancel(preview_timer)
                except tk.TclError:pass
                preview_timer=None
            if model is None:
                preview_name.set('No character selected');set_preview_message('Select a character to preview');return
            preview_name.set(player_models.display_name(model));preview_type.set('Loading field animation…');set_preview_message('Loading from game…')
            def start_preview():
                nonlocal preview_timer
                preview_timer=None
                if not window.winfo_exists() or generation!=preview_generation:return
                def read_preview():
                    try:result_queue.put(('preview',generation,model,player_models.load_preview(source,model)))
                    except Exception as exc:result_queue.put(('preview_error',generation,model,str(exc)))
                threading.Thread(target=read_preview,daemon=True).start()
            preview_timer=window.after(180,start_preview)
        def refresh_presets():
            names=['Choose a saved look…']+[item['name'] for item in self.preference_values.get('player_model_presets',[])]
            preset_box['values']=names
            if not presets.get() or presets.get() not in names:preset_box.current(0)
        def save_preset():
            model=current_choice();name=preset_name.get().strip()[:model_preferences.MAX_PRESET_NAME]
            if model is None:state.configure(text='Select a character before saving a look.');return
            if not name:state.configure(text='Enter a name for this saved look.');return
            saved=model_preferences.normalize_presets(self.preference_values.get('player_model_presets',[]))
            existing=next((i for i,item in enumerate(saved) if item['name'].casefold()==name.casefold()),None)
            if existing is None and len(saved)>=model_preferences.MAX_PRESETS:
                state.configure(text=f'You can save up to {model_preferences.MAX_PRESETS} looks. Delete one to make room.');return
            item={'name':name,'model_id':model}
            if existing is None:saved.append(item)
            else:saved[existing]=item
            self.preference_values['player_model_presets']=saved;self._save();refresh_presets();presets.set(name);state.configure(text=f'Saved “{name}” to this game profile.')
        def apply_preset():
            name=presets.get()
            if not name or name=='Choose a saved look…':state.configure(text='Choose a saved look first.');return
            item=next((item for item in self.preference_values.get('player_model_presets',[]) if item['name']==name),None)
            if item is None:return
            model=item['model_id']
            if model and model not in models:state.configure(text='This saved character is not in the selected game.');return
            self.preference_values['player_model']=model;self._refresh_player_model_label();self._save();self.status.set(f'Saved look “{name}” selected · applies next launch.');close_picker()
        def delete_preset():
            name=presets.get()
            if not name or name=='Choose a saved look…':state.configure(text='Choose a saved look to remove.');return
            self.preference_values['player_model_presets']=[item for item in self.preference_values.get('player_model_presets',[]) if item['name']!=name]
            self._save();refresh_presets();state.configure(text=f'Removed saved look “{name}”.')
        def toggle_favorite():
            model=current_choice()
            if model is None:return
            favorites=model_preferences.normalize_favorites(self.preference_values.get('player_model_favorites',[]))
            if model in favorites:favorites.remove(model)
            else:
                if len(favorites)>=model_preferences.MAX_FAVORITES:state.configure(text=f'You can keep up to {model_preferences.MAX_FAVORITES} favorites.');return
                favorites.append(model)
            self.preference_values['player_model_favorites']=favorites;self._save();populate();request_preview();state.configure(text='Favorites saved to this game profile.')
        def choose_random():
            if not ready or not visible:state.configure(text='No characters match the current filters.');return
            model=random.choice(visible)
            self.preference_values['player_model']=model;self._refresh_player_model_label();self._save();self.status.set('Random field character selected · applies next launch.');close_picker()
        def apply_selection():
            if not ready:return
            model=current_choice()
            if model is None:return
            self.preference_values['player_model']=model;self._refresh_player_model_label();self._save()
            self.status.set('Character saved · applies next launch.');close_picker()
        def use_default():
            self.preference_values['player_model']=0;self._refresh_player_model_label();self._save()
            self.status.set('Default character selected · applies next launch.');close_picker()
        def poll_queue():
            nonlocal ready,active_frames,queue_poll
            if not window.winfo_exists():return
            try:
                while True:
                    item=result_queue.get_nowait();kind=item[0]
                    if kind=='models':
                        ready=True;models.extend(item[1]);populate();state.configure(text=f'{len(models)} animated field characters available.');entry.focus_set();request_preview()
                    elif kind=='error':
                        ready=True;state.configure(text='Could not read models: '+str(item[1]))
                    elif kind in ('preview','preview_error'):
                        _kind,generation,model,value=item
                        if generation!=preview_generation or model!=current_choice():continue
                        if kind=='preview_error':set_preview_message('Preview not available');preview_type.set(str(value))
                        else:
                            active_frames,label_text=value;preview_type.set(label_text+' · native game frames');play_preview()
            except queue.Empty:pass
            queue_poll=window.after(100,poll_queue)
        query.trace_add('write',populate)
        category.trace_add('write',populate);sort.trace_add('write',populate)
        choices.bind('<Double-Button-1>',lambda _event:apply_selection())
        choices.bind('<<ListboxSelect>>',request_preview)
        category_box.bind('<<ComboboxSelected>>',populate);sort_box.bind('<<ComboboxSelected>>',populate)
        window.protocol('WM_DELETE_WINDOW',close_picker)
        window._launcher_close=close_picker
        favorite_button=button(browse,'Add favorite',toggle_favorite);favorite_button.pack(side='right')
        button(preset_row,'Save look',save_preset).pack(side='left',padx=(8,0))
        button(preset_row,'Apply',apply_preset).pack(side='left',padx=(8,0),after=preset_box)
        button(preset_row,'Remove',delete_preset).pack(side='left',padx=(6,0),after=preset_box)
        actions=tk.Frame(outer,bg=C['background']);actions.pack(fill='x',pady=(10,0))
        button(actions,'Default',use_default).pack(side='left')
        button(actions,'Random from results',choose_random).pack(side='left',padx=(8,0))
        button(actions,'Use selected',apply_selection,kind='primary').pack(side='right')
        poll_queue()

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
            if isinstance(data.get('preferences'),dict):self.preference_values=services.normalize_preferences(data['preferences'])
            if isinstance(data.get('cheats'),dict):self.cheat_choices={k:{ident:flag for ident,flag in v.items() if ident in self.cheat_vars_ids() and type(flag) is bool} for k,v in list(data['cheats'].items())[-32:] if isinstance(k,str) and len(k)<=32 and isinstance(v,dict)}
            acknowledgment=data.get('tailscale_guide_ack','')
            if isinstance(acknowledgment,str) and re.fullmatch(r'[a-f0-9]{64}',acknowledgment):self.tailscale_guide_ack=acknowledgment
        except (OSError,ValueError,AttributeError):pass

    def _save(self):
        if self._switching:return
        if self.play_profiles:
            item=self._active_profile();item['rom']=self.rom.get();item['preferences']=dict(self.preference_values)
        try:
            prefs.atomic(self.config_path,json.dumps({'selected_game':self.selected_game.get(),'research_root':self.research_root.get(),'research_mode':self.research_mode.get(),'research_address':self.research_address.get(),'rom':self.rom.get(),'check':self.auto.get(),'music':self.music.get(),'preferences':self.preference_values,'cheats':self.cheat_choices,'profiles':self.play_profiles,'active_profile':self.active_profile_id,'tailscale_guide_ack':self.tailscale_guide_ack}))
        except OSError as exc:self.status.set('Could not save settings: '+str(exc))

    def _sync(self):
        self._sync_activity()
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

    def _sync_activity(self):
        active=self.busy or self.guides_busy
        if active and not self._activity_running:
            self.footer_activity.pack(side='right',padx=(0,12))
            self.footer_activity.start(14);self._activity_running=True
        elif not active and self._activity_running:
            self.footer_activity.stop();self.footer_activity.pack_forget();self._activity_running=False

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

    def _navigation_groups(self):
        if self.active_mod=='black2':
            return (
                ('MOD LIBRARY',('Library',)),
                ('PLAY',('Play','Co-op','Features')),
                ('MANAGE',('Profiles','News','Updates','Tools','Setup','Settings')),
            )
        if self.active_mod=='pokemon-x':
            return (('MOD LIBRARY',('Library',)),('EXPERIMENTAL',('XPlay','XCoop','XGuides')))
        return (('MOD LIBRARY',('Library',)),)

    def _highlight_navigation(self,name):
        for key,control in self.nav.items():
            selected=key==name
            control.configure(
                bg=C['navSelected'] if selected else C['nav'],
                fg=C['navSelectedText'] if selected else C['navText'],
                activebackground=C['navSelected'] if selected else C['navHover'],
                activeforeground=C['navSelectedText'] if selected else C['navText'],
                highlightbackground=C['navSelected'] if selected else C['nav'],
                image=self.nav_cursor if selected else '',compound='left')

    def _apply_navigation(self):
        groups=self._navigation_groups()
        self.visible_pages=tuple(name for _,names in groups for name in names)
        for section in self.nav_sections.values():section.pack_forget()
        for name,control in self.nav.items():
            control.pack_forget()
        for group,names in groups:
            self.nav_sections[group].pack(fill='x',padx=22,pady=(3,1))
            for name in names:self.nav[name].pack(fill='x',padx=10,pady=1)
        self.mod_caption.configure(text=game_routes.MODS[self.active_mod]['name'] if self.active_mod else 'MULTIPLAYER MODS')
        self.footer_version.configure(text=self._version_text() if self.active_mod=='black2' else 'Pokemon X · Prototype' if self.active_mod else 'Multiplayer mod library')
        if self.page_name:self._highlight_navigation(self.page_name)

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
        if self.net_mode.get()=='Tailscale backup' and not self._require_tailscale_guide_review():return
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
            if self.net_mode.get()=='Tailscale backup' and not self._require_tailscale_guide_review():return
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
            launch_context={
                'exe':exe,'path':path,'settings':settings,'selected':dict(selected),
                'profile':dict(self.profile) if self.profile else None,'item':dict(item),
                'network':dict(net),'model_id':model_id,'lan_action':lan_action,
            }
            self.status.set('Preparing Cynthia’s Route 7 event in the background…')
            self._launch_context=launch_context
            self._worker('launch-preparation',lambda:self._prepare_launch_rom(path,model_id,settings.get('area_scenery',False)))
        except (OSError,ValueError,subprocess.SubprocessError) as exc:
            self._stop_game_workers();self.status.set('Unable to start the game: '+str(exc))

    def _prepare_launch_rom(self,path,model_id,area_scenery=False):
        """Perform disk-heavy launch preparation away from Tk's event loop."""
        try:
            launch_rom=cynthia_event.prepare_variant(path,self.home)
            story_message=''
        except cynthia_event.UnsupportedRomError as exc:
            launch_rom=path
            story_message=str(exc)+' The game will start without the Route 7 event.'
        if model_id:
            self.messages.put(('launch-status','Preparing your selected field character…'))
            launch_rom=player_models.prepare_variant(launch_rom,self.home,model_id)
        area_catalog=''
        if area_scenery:
            self.messages.put(('launch-status','Preparing nearby battle scenery in the background…'))
            from area_scene_cache import prepare_catalog
            area_catalog=str(prepare_catalog(path,self.home/'area-scenes'))
        return {'rom':str(launch_rom),'story_message':story_message,'area_catalog':area_catalog}

    def _start_prepared_game(self,context,prepared):
        """Finish launch setup on the UI thread after the ROM copy is ready."""
        exe=context['exe'];path=context['path'];settings=context['settings'];item=context['item'];net=context['network']
        launch_rom=Path(prepared['rom'])
        try:
            prefs.apply(exe.parent,path,settings,context['selected'],context['profile'],self.home)
            self._apply_save_folder(exe.parent,item,default_directory=path.parent if (context['model_id'] or launch_rom != path) else None)
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
                area_catalog=prepared.get('area_catalog')
                if not area_catalog:raise ValueError('Nearby battle scenery was not prepared.')
                env['UNOVA_AREA_CATALOG']=str(area_catalog)
                from battle_surroundings_worker import SurroundingsWorker
                directory=Path(env['UNOVA_AREA_CATALOG']).parent/'nearby'
                self.surroundings_worker=SurroundingsWorker(path,directory)
                env['UNOVA_SURROUNDINGS_DIR']=str(directory)
            for key in ('UNOVA_LAN_ACTION','UNOVA_LAN_HOST','UNOVA_LAN_REQUEST','UNOVA_LAN_SLOTS'):env.pop(key,None)
            self.lan_request=''
            lan_action=context['lan_action']
            if lan_action:
                self.lan_request=uuid.uuid4().hex;self.lan_started=time.monotonic();self.lan_was_connected=False
                env.update({'UNOVA_LAN_ACTION':lan_action,'UNOVA_LAN_HOST':net['host'],'UNOVA_LAN_REQUEST':self.lan_request,'UNOVA_LAN_SLOTS':str(item.get('lan_slots',16))})
                self.lan_status.set('Starting LAN host…' if lan_action=='host' else 'Joining LAN host…')
            self._stop_music()
            self.game=subprocess.Popen([str(exe),str(launch_rom.resolve())],cwd=exe.parent,env=env)
            message=('Game running. '+prepared['story_message'] if prepared.get('story_message')
                     else 'Game running. Save normally and close it before starting another session.')
            self.status.set(message);self._sync()
        except (OSError,ValueError,subprocess.SubprocessError) as exc:
            self._stop_game_workers();self.status.set('Unable to start the game: '+str(exc));self._sync()

    def guide(self,name='PLAYER_GUIDE.md'):
        if name not in services.GUIDES:return
        guide=services.cached_guide(self.home,name) or self.root/'docs'/name
        try:
            if guide.is_file():os.startfile(str(guide))
            else:webbrowser.open('https://github.com/'+updates.REPO+'/blob/main/docs/'+name)
        except OSError as exc:self.status.set('Could not open the guide: '+str(exc))

    def refresh_guides(self):
        if self.guides_busy:return
        self.guides_busy=True;self.guide_status.set('Checking GitHub guides…');self._sync()
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
        # Schedule first so an unexpected callback error cannot permanently
        # stop the message pump and leave background work looking unfinished.
        self.after(100,self._poll)
        try:
            while True:
                action,value=self.messages.get_nowait()
                if action in ('guides','guides-offline'):
                    self.guides_busy=False;self.guide_status.set('Guides up to date' if action=='guides' else 'Offline · using saved guides');self._sync();continue
                if action=='launch-status':
                    self.status.set(value);continue
                if action=='storage-progress':
                    self._storage_progress(value);continue
                if action=='progress':
                    self.bar['value']=value
                    if not self.cancel.is_set():self.phase.set('Verifying and preparing update…' if value>=100 else f'Downloading · {value:.0f}%')
                    continue
                if action=='feature-mega-frames':
                    try:
                        self.feature_mega_frames=value;self.feature_mega_photos=[]
                        for widget,frames in zip(self.feature_mega_labels,self.feature_mega_frames):
                            photo=ImageTk.PhotoImage(frames[0],master=self);self.images.append(photo);self.feature_mega_photos.append(photo)
                            widget.configure(image=photo)
                        self.feature_mega_loaded=True;self.feature_mega_loading=False
                        self.feature_art_status.configure(text='Animated Mega Mawile previews ready.')
                        for photo in self.feature_mega_static:
                            if photo in self.images:self.images.remove(photo)
                        self.feature_mega_static=[]
                        self._set_feature_mega_animation(self.page_name=='Features')
                    except (tk.TclError,OSError,ValueError) as exc:
                        self.feature_mega_loading=False;self.feature_art_status.configure(text='Animation preview unavailable; showing stills.')
                        self.status.set('Could not load Mega Mawile animation preview: '+str(exc))
                    continue
                if action=='feature-mega-error':
                    self.feature_mega_loading=False;self.feature_art_status.configure(text='Animation preview unavailable; showing stills.')
                    continue
                finished_operation=self.operation;self.busy=False;self.operation=''
                if action=='launch-preparation':
                    context=getattr(self,'_launch_context',None);self._launch_context=None
                    if context is None:self.status.set('Unable to start the game: launch details expired.');self._sync();continue
                    try:self._start_prepared_game(context,value)
                    except Exception as exc:
                        try:self._stop_game_workers()
                        except Exception as cleanup_error:exc=RuntimeError(f'{exc}; scenery worker cleanup also failed: {cleanup_error}')
                        if self.game is not None and self.game.poll() is None:
                            self.status.set('Game started, but launcher setup did not finish: '+str(exc))
                        else:
                            self.status.set('Unable to start the game: '+str(exc))
                        self._sync()
                    continue
                if action=='error' and finished_operation=='launch-preparation':
                    self._launch_context=None;self.status.set('Unable to prepare the game: '+value);self._sync();continue
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
        self._reap_game_workers();self._read_lan_status();self._sync()

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
        self._heading(parent,'FEATURES','Features','A quick guide to what you can do in Unova Together.')
        banner=tk.Frame(parent,bg=C['hero'],height=132);banner.pack(fill='x',pady=(0,14));banner.pack_propagate(False)
        copy=tk.Frame(banner,bg=C['hero']);copy.pack(side='left',fill='both',expand=True,padx=20,pady=18)
        label(copy,'EXPLORE TOGETHER',size=9,bold=True,color=C['accent'],bg=C['hero']).pack(anchor='w')
        label(copy,'Make Unova your own',size=17,bold=True,color=C['surface'],bg=C['hero'],role='display').pack(anchor='w',pady=(7,4))
        note=label(copy,'Mega Evolution, co-op, animated followers and more.',size=10,color=C['accent'],bg=C['hero'],wraplength=480,justify='left')
        note.pack(anchor='w')
        copy.bind('<Configure>',lambda e,w=note:w.configure(wraplength=max(220,e.width-4)))
        fan_art=tk.Frame(banner,bg=C['hero']);fan_art.pack(side='right',padx=(0,14),pady=4)
        label(fan_art,'MEGA AMPHAROS · GEN 5 STYLE',size=8,bold=True,color=C['accent'],bg=C['hero']).pack(anchor='center',pady=(0,1))
        fan_sprites=tk.Frame(fan_art,bg=C['hero']);fan_sprites.pack()
        for filename in ('mega-ampharos-front.gif','mega-ampharos-back.gif'):
            picture=tk.PhotoImage(file=HERE/'assets/features/gen5-fan'/filename,format='gif -index 0')
            self.images.append(picture);self.feature_gen5_art.append(picture)
            tk.Label(fan_sprites,image=picture,bg=C['hero'],bd=0).pack(side='left',padx=2)

        grid=tk.Frame(parent,bg=C['background']);grid.pack(fill='x')
        self.feature_grid=grid;self.feature_grid_columns=0;self.feature_cards=[]
        mega=card(grid);self.feature_cards.append(mega)
        layout=tk.Frame(mega,bg=C['surface']);layout.pack(fill='x',padx=16,pady=14)
        art=tk.Frame(layout,bg=C['surface']);self.feature_mega_art=art
        for side,filename in (('FRONT','mega-mawile-front.gif'),('BACK','mega-mawile-back.gif')):
            pose=tk.Frame(art,bg=C['surface']);pose.pack(side='left',padx=(0,12))
            label(pose,side,size=8,color=C['muted'],bg=C['surface']).pack(anchor='center')
            photo=tk.PhotoImage(file=HERE/'assets/features'/filename,format='gif -index 0').zoom(2,2)
            self.images.append(photo);self.feature_mega_static.append(photo)
            sprite=tk.Label(pose,image=photo,bg=C['surface'],bd=0);sprite.pack()
            self.feature_mega_labels.append(sprite)
        details=tk.Frame(layout,bg=C['surface']);self.feature_mega_details=details
        label(details,'MEGA EVOLUTION',size=9,bold=True,color=C['primary'],bg=C['surface']).pack(anchor='w')
        label(details,'49 Mega forms',size=16,bold=True,bg=C['surface'],role='display').pack(anchor='w',pady=(5,3))
        mega_copy=label(details,'Give it the matching stone, then press L + R during move selection. Mega Evolution lasts until battle ends.',size=10,color=C['muted'],bg=C['surface'],wraplength=520,justify='left')
        mega_copy.pack(anchor='w',fill='x',pady=(0,5))
        label(details,'Examples: Serperior · Charizard Y · Salamence',size=9,bg=C['surface']).pack(anchor='w')
        self.feature_art_status=label(details,'Animated previews load when you open this page.',size=8,color=C['muted'],bg=C['surface'])
        self.feature_art_status.pack(anchor='w',pady=(5,0))
        details.bind('<Configure>',lambda e,w=mega_copy:w.configure(wraplength=max(100,e.width-8)),add='+')
        def arrange_mega(event):
            horizontal=event.width>=650
            if getattr(layout,'_horizontal',None)==horizontal:return
            layout._horizontal=horizontal
            art.pack_forget();details.pack_forget()
            if horizontal:
                art.pack(side='left',anchor='n',padx=(0,16));details.pack(side='left',fill='x',expand=True)
            else:
                art.pack(side='top',anchor='center',pady=(0,10));details.pack(side='top',fill='x',expand=True)
        layout.bind('<Configure>',arrange_mega,add='+')

        entries=(
            ('STORY','Cynthia’s Route 7 challenge','After Skyla, meet Cynthia near Route 7 for a Mega Stone. Return later to face her team and Mega Garchomp; the launcher prepares the event-ready game copy.'),
            ('CO-OP','Play with friends','See teammates, trade Pokémon, share items and battle supported trainers. Co-op XP is disabled to protect save consistency.'),
            ('POKÉMON','Following Pokémon','Animated followers include separate shiny sprites. Adjust follower motion in launcher Settings.'),
            ('CUSTOMIZE','Field models & camera','Choose a valid animated character from your game, save favorite looks, and adjust camera tilt, rotation and zoom.'),
            ('TEAM TOOLS','Encounters, moves & stats','Find wild encounters, relearn level-up moves, view IVs and EVs, and use supported field HMs.'),
            ('SAVES','Profiles & backups','Keep separate save slots, create backups, restore a save, and clean old installations while keeping your progress.'),
            ('BATTLES','Optional battle scenery','Build nearby battle backgrounds from your own game file. This optional feature is experimental.'),)
        for category,title,description in entries:
            panel=card(grid);self.feature_cards.append(panel)
            body=tk.Frame(panel,bg=C['surface']);body.pack(fill='both',expand=True,padx=16,pady=14)
            label(body,category,size=8,bold=True,color=C['primary'],bg=C['surface'],role='utility').pack(anchor='w')
            label(body,title,size=13,bold=True,bg=C['surface']).pack(anchor='w',pady=(5,4))
            text=label(body,description,size=10,color=C['muted'],bg=C['surface'],wraplength=360,justify='left')
            text.pack(anchor='w',fill='x')
            body.bind('<Configure>',lambda e,w=text:w.configure(wraplength=max(200,e.width-4)),add='+')
        grid.bind('<Configure>',self._layout_feature_grid,add='+')
        guides=tk.Frame(parent,bg=C['background']);guides.pack(fill='x',pady=(14,4))
        guide_rows=(('Feature guide','FEATURES.md'),('Mega Evolution','MEGA_EVOLUTION.md'),('Follower interactions','COMPANION_INTERACTIONS.md'))
        for title,doc in guide_rows:
            button(guides,title,lambda name=doc:self.guide(name)).pack(side='left',padx=(0,8))
        more=tk.Frame(parent,bg=C['background']);more.pack(fill='x',pady=(0,12))
        for title,doc in (('Known issues','KNOWN_ISSUES.md'),('Roadmap','ROADMAP.md')):
            button(more,title,lambda name=doc:self.guide(name)).pack(side='left',padx=(0,8))

    def _layout_feature_grid(self,event):
        columns=2 if event.width>=640 else 1
        if columns==self.feature_grid_columns:return
        self.feature_grid_columns=columns
        self.feature_grid.grid_columnconfigure(0,weight=1,uniform='feature-card')
        self.feature_grid.grid_columnconfigure(1,weight=1 if columns==2 else 0,uniform='feature-card' if columns==2 else '')
        for index,panel in enumerate(self.feature_cards):
            if columns==2 and index==0:row,column,span=0,0,2
            elif columns==2:row,column,span=1+(index-1)//2,(index-1)%2,1
            else:row,column,span=index,0,1
            panel.grid(row=row,column=column,columnspan=span,sticky='ew',padx=(0,8) if columns==2 and column==0 and span==1 else (8,0) if columns==2 and column==1 else 0,pady=(0,10))

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
        for photo,frames in zip(self.feature_mega_photos,self.feature_mega_frames):
            photo.paste(frames[self.feature_mega_frame])
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
        for child in list(self.winfo_children()):
            close_dialog=getattr(child,'_launcher_close',None)
            if callable(close_dialog):
                try:close_dialog()
                except tk.TclError:pass
        for token in self.tk.call('after','info'):self.after_cancel(token)
        super().destroy()
