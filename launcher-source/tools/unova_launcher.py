"""Unova Together launcher. Original contributions by mvq1303 / WhatWasMissing."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import unova_updater as updates

from launcher_ui.app import Launcher

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--home',type=Path);parser.add_argument('--self-test',type=Path)
    parser.add_argument('--presence-relay',type=int,metavar='PORT')
    parser.add_argument('--scenery-self-test',type=Path,metavar='ROM',help='Generate local scenery during --self-test')
    parser.add_argument('--gen5-self-test',type=Path,metavar='ROM',help='Inspect ROM and calculate Challenge curve during --self-test')
    parser.add_argument('--save-pair',type=Path,nargs=2,help='Compare two saves during --self-test')
    args=parser.parse_args()
    if args.presence_relay is not None:
        if not 1<=args.presence_relay<=65535:parser.error('Relay port must be 1–65535.')
        import asyncio
        from presence_server import run
        asyncio.run(run('0.0.0.0',args.presence_relay));return
    executable=Path(sys.executable if getattr(sys,'frozen',False) else __file__).resolve()
    installed_unova=Path('F:/unova-together')
    home=(args.home or (installed_unova if (installed_unova/'builds/current/melonDS.exe').is_file() else executable.parent.parent)).resolve()
    root=updates.active_root(home,allow_missing=True)
    # The shared hub owns navigation. A mod update must not delegate to its older launcher.
    app=Launcher(home,testing=bool(args.self_test))
    if args.self_test:
        def verify():
            app.update_idletasks()
            result={'title':app.title(),'startupPage':app.page_name,'modLibrary':list(app.library_buttons),'version':app._version_text(),'playDisabledWithoutROM':str(app.play['state'])=='disabled','updateCheckAvailable':str(app.check_button['state'])=='normal','windowCreated':app.winfo_exists()==1,'pages':list(app.pages),'offlineNews':len(app.news),'artworkLoaded':len(app.images)}
            app._open_mod('black2',save=False)
            def widget_texts(widget):
                values=[]
                try: values.append(str(widget.cget('text')))
                except Exception: pass
                for child in widget.winfo_children():values.extend(widget_texts(child))
                return values
            credit_text='\n'.join(widget_texts(app))
            result['experimentalControlsPresent']='Companion interactions' in credit_text
            result['companionExperimentEnabled']=app.companion_interactions.get()
            result['soaringOptionRemoved']='Latias / Latios flight preview' not in credit_text
            result['playtesterCreditsVisible']=all(name in credit_text for name in ('maxback221','randomitem19'))
            result['cleanupButtonPresent']='Clean old installations' in credit_text
            credit_sizes=[]
            for width,height in ((1040,790),(900,680),(1280,850)):
                app.geometry(f'{width}x{height}');app.update()
                widget=app.playtester_credit
                credit_sizes.append(widget.winfo_ismapped() and widget.winfo_rooty()>=app.winfo_rooty() and widget.winfo_rooty()+widget.winfo_height()<=app.winfo_rooty()+app.winfo_height() and widget.winfo_reqheight()<=widget.winfo_height())
            result['playtesterCreditsFitWindowSizes']=all(credit_sizes)
            from launcher_ui.settings_editor import SettingsEditor
            editor=SettingsEditor(app,root/'builds/current');editor.update_idletasks()
            result['emulatorSettings']=len(editor.tree.get_children());editor.destroy()
            if args.gen5_self_test:
                from launcher_ui import gen5_tools
                result['romCompatibility']=gen5_tools.compatibility(args.gen5_self_test)
                result['challengeProgression']=gen5_tools.progression(args.gen5_self_test,25)
            if args.save_pair:
                from launcher_ui import gen5_tools
                result['saveComparison']=gen5_tools.compare_saves(*args.save_pair)
            if args.scenery_self_test:
                from area_scene_cache import prepare_catalog
                manifest=prepare_catalog(args.scenery_self_test,home/'area-scenes')
                result['sceneryCoverage']=json.loads(manifest.read_text())['coverage']
                result['sceneryCacheReused']=prepare_catalog(args.scenery_self_test,home/'area-scenes')==manifest
            args.self_test.write_text(json.dumps(result),encoding='utf-8');app.destroy()
        app.after(300,verify)
    app.mainloop()

if __name__=='__main__':main()
