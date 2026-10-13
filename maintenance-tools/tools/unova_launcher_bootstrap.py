"""Stable shared launcher and one-time legacy client repair. mvq1303."""
from pathlib import Path
import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import launcher_migration as migration


def repair_gui(home=None, entry=None):
    import tkinter as tk
    from tkinter import filedialog,messagebox
    root=tk.Tk();root.withdraw()
    if entry is None:
        selected=filedialog.askopenfilename(parent=root,title='Select the OLD Pokemon Together.exe used by your shortcut',filetypes=[('Shared launcher','Pokemon Together.exe')])
        if not selected:root.destroy();return
        entry=Path(selected)
    if home is None:
        try:home=Path(migration.read(Path(entry).parent/migration.SIDECAR)['home'])
        except (OSError,ValueError,KeyError):
            candidate=Path(entry).parent.parent
            try:migration.active_launcher(candidate);home=candidate
            except (OSError,ValueError):
                selected=filedialog.askdirectory(parent=root,title='Select your existing Unova Together installation (contains .updates or builds)')
                if not selected:root.destroy();return
                home=Path(selected)
    root.title('Pokemon Together · Repair launcher');root.geometry('540x200');root.resizable(False,False);root.deiconify()
    state=tk.StringVar(value='Repairing your original launcher entry point…')
    tk.Label(root,textvariable=state,wraplength=490,justify='left',font=('Segoe UI',11)).pack(padx=24,pady=26,fill='x')
    tk.Label(root,text='Profiles, saves and game files stay in their existing installation.',wraplength=490,font=('Segoe UI',9)).pack(padx=24)
    events=queue.Queue()
    def work():
        try:
            migration.migrate(home,entry,Path(sys.executable),timeout=120,status=lambda text:events.put(('status',text)))
            events.put(('done','Repaired. Close this window and use your usual launcher shortcut.'))
        except Exception as exc:events.put(('error',str(exc)))
    def poll():
        try:
            while True:
                kind,text=events.get_nowait();state.set(text)
                if kind in ('done','error'):
                    close.configure(state='normal');root.protocol('WM_DELETE_WINDOW',root.destroy)
                    return
        except queue.Empty:pass
        root.after(150,poll)
    close=tk.Button(root,text='Close',state='disabled',command=root.destroy);close.pack(pady=16)
    root.protocol('WM_DELETE_WINDOW',lambda:state.set('Repair is running. Close the old launcher window if requested.'))
    threading.Thread(target=work,daemon=True).start();root.after(100,poll);root.mainloop()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--home',type=Path);parser.add_argument('--entry',type=Path)
    parser.add_argument('--migrate',action='store_true');parser.add_argument('--repair',action='store_true')
    parser.add_argument('--timeout',type=float,default=0);parser.add_argument('--self-test',type=Path)
    args,forward=parser.parse_known_args()
    if args.migrate:
        if args.home is None or args.entry is None:parser.error('--migrate requires --home and --entry')
        try:migration.migrate(args.home,args.entry,sys.executable,timeout=args.timeout)
        except Exception as exc:
            migration.atomic(args.home/'.updates'/migration.REPORT,{'schema':1,'product':migration.PRODUCT,'state':'failed','error':str(exc)})
            raise
        return
    if args.repair or Path(sys.executable).name.lower()=='repair-launcher.exe':
        repair_gui(args.home,args.entry);return
    home,root,target=migration.bootstrap_target(sys.executable,args.home)
    command=[str(target),'--home',str(home),*forward]
    if args.self_test:command+=['--self-test',str(args.self_test)]
    env=dict(os.environ,PYINSTALLER_RESET_ENVIRONMENT='1')
    if args.self_test:subprocess.run(command,cwd=root,env=env,check=True,timeout=45)
    else:subprocess.Popen(command,cwd=root,env=env)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        if '--migrate' not in sys.argv:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,str(exc),'Pokemon Together launcher',0x10)
        raise SystemExit(1)
