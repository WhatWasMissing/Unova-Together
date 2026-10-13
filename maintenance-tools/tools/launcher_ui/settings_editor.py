"""Complete native-config editor; game saves stay game-owned. mvq1303."""
from pathlib import Path
import json,math,tkinter as tk
from tkinter import ttk
from collections.abc import Mapping
import tomlkit
from . import preferences as prefs
from .components import C,F,HERE,button,label

SCHEMA=json.loads((HERE/'assets/emulator-settings.json').read_text())['settings']

def put(doc,path,value):
    parts=path.split('.');table=doc
    for part in parts[:-1]:table=table.setdefault(part,tomlkit.table())
    table[parts[-1]]=value

def document(runtime):
    doc=prefs.read_document(runtime)
    for path,item in SCHEMA.items():
        parts=path.split('.');value=doc
        for part in parts:
            if not isinstance(value,Mapping) or part not in value:
                put(doc,path,item['default']);break
            value=value[part]
    return doc

def rows(doc,prefix=''):
    result=[]
    for key,value in doc.items():
        path=prefix+key
        if isinstance(value,Mapping):result+=rows(value,path+'.')
        else:result.append((path,value))
    return result

def literal(value):
    doc=tomlkit.document();doc['value']=value
    return tomlkit.dumps(doc).split('=',1)[1].strip()

def validate(text):
    if len(text.encode('utf-8'))>2*1024*1024:raise ValueError('Settings file is too large.')
    try:doc=tomlkit.parse(text)
    except Exception as exc:raise ValueError('Invalid settings: '+str(exc)) from exc
    for path,value in rows(doc):
        if any(key.startswith(path+'.') for key in SCHEMA):raise ValueError(path+': this must be a settings section, not a value.')
        native=value.unwrap() if hasattr(value,'unwrap') else value
        schema=SCHEMA.get(path)
        if schema:
            expected={'int':int,'float':(int,float),'bool':bool,'str':str,'array':list}[schema['type']]
            if not isinstance(native,expected) or isinstance(native,bool) and schema['type']!='bool':raise ValueError(path+': incorrect value type.')
        if isinstance(native,float) and not math.isfinite(native):raise ValueError(path+': enter a finite number.')
        if isinstance(native,int) and not isinstance(native,bool) and not -(2**63)<=native<2**63:raise ValueError(path+': number is too large.')
        if path in ('TargetFPS','FastForwardFPS','SlowmoFPS') and native<=0:raise ValueError(path+': frame rate must be positive.')
    return doc

def save(runtime,text):
    runtime=Path(runtime)
    if prefs.running(runtime/'melonDS.exe'):raise ValueError('Close this build’s game before saving emulator settings.')
    doc=validate(text);path=runtime/'melonDS.toml'
    if path.exists():prefs.atomic(path.with_name('melonDS.toml.before-all-settings'),path.read_text(encoding='utf-8-sig'))
    prefs.atomic(path,tomlkit.dumps(doc))
    return doc

class SettingsEditor(tk.Toplevel):
    def __init__(self,owner,runtime):
        doc=document(runtime)
        super().__init__(owner);self.owner=owner;self.runtime=Path(runtime);self.doc=doc
        self.title('Unova Together · Emulator settings');self.geometry('860x650');self.minsize(700,500);self.configure(bg=C['background'])
        self.transient(owner);self.status=tk.StringVar(value='Changes apply next launch. Profiles control save folders and optional cheats.')
        label(self,'All emulator settings',size=22,bold=True,role='display').pack(anchor='w',padx=20,pady=(18,6))
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True,padx=20)
        settings=tk.Frame(self.tabs,bg=C['background']);raw=tk.Frame(self.tabs,bg=C['background']);self.tabs.add(settings,text='Find a setting');self.tabs.add(raw,text='Full configuration')
        label(settings,'Search settings',size=10).pack(anchor='w',pady=(10,2))
        self.search=tk.StringVar();ttk.Entry(settings,textvariable=self.search).pack(fill='x',pady=(0,10));self.search.trace_add('write',lambda *_:self.refresh())
        listing=tk.Frame(settings,bg=C['background']);listing.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(listing,columns=('value',),show='tree headings',selectmode='browse');self.tree.heading('#0',text='Setting');self.tree.heading('value',text='Value');self.tree.column('#0',width=380);self.tree.column('value',width=260)
        scroll=ttk.Scrollbar(listing,orient='vertical',command=self.tree.yview);self.tree.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.tree.pack(fill='both',expand=True);self.tree.bind('<<TreeviewSelect>>',self.select)
        self.selected=tk.StringVar(value='Select a setting');label(settings,textvariable=self.selected,size=10).pack(anchor='w',pady=(10,3))
        self.value=tk.StringVar();self.entry=ttk.Entry(settings,textvariable=self.value);self.entry.pack(fill='x');self.entry.bind('<Return>',lambda _:self.stage())
        button(settings,'Apply value',self.stage).pack(anchor='w',pady=8)
        self.text=tk.Text(raw,wrap='none',font=(F['utility'],10),undo=True);ys=ttk.Scrollbar(raw,command=self.text.yview);xs=ttk.Scrollbar(raw,orient='horizontal',command=self.text.xview);self.text.configure(yscrollcommand=ys.set,xscrollcommand=xs.set);xs.pack(side='bottom',fill='x');ys.pack(side='right',fill='y');self.text.pack(fill='both',expand=True)
        self.text.insert('1.0',tomlkit.dumps(self.doc));self.tabs.bind('<<NotebookTabChanged>>',self.changed_tab)
        actions=tk.Frame(self,bg=C['background']);actions.pack(fill='x',padx=20,pady=10);button(actions,'Save settings',self.commit,kind='primary').pack(side='left');button(actions,'Close',self.destroy).pack(side='left',padx=8)
        label(self,textvariable=self.status,size=10,color=C['muted'],wraplength=800,justify='left').pack(fill='x',padx=20,pady=(0,12));self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children());query=self.search.get().casefold()
        for path,value in rows(self.doc):
            if query in path.casefold():self.tree.insert('', 'end',iid=path,text=path,values=(literal(value),))
    def select(self,event=None):
        selected=self.tree.selection()
        if selected:self.selected.set(selected[0]);self.value.set(literal(dict(rows(self.doc))[selected[0]]))
    def stage(self):
        path=self.selected.get()
        if path not in dict(rows(self.doc)):return
        try:
            value=tomlkit.parse('value = '+self.value.get())['value'];candidate=tomlkit.parse(tomlkit.dumps(self.doc));put(candidate,path,value);validate(tomlkit.dumps(candidate));self.doc=candidate
            self.text.delete('1.0','end');self.text.insert('1.0',tomlkit.dumps(self.doc));self.refresh();self.status.set('Value staged. Save settings to apply it next launch.')
        except (ValueError,TypeError,tomlkit.exceptions.ParseError) as exc:self.status.set(str(exc))
    def changed_tab(self,event=None):
        if self.tabs.index(self.tabs.select())==0:
            try:self.doc=validate(self.text.get('1.0','end-1c'));self.refresh()
            except ValueError as exc:self.status.set(str(exc));self.tabs.select(1)
    def commit(self):
        try:
            self.doc=save(self.runtime,self.text.get('1.0','end-1c'))
            values=prefs.defaults(self.runtime);self.owner.preference_values.update(values);self.owner.pause.set(values['pause']);self.owner.filter.set(values['filter']);self.owner.volume.set(values['volume']);self.owner._save()
            folder=str(self.doc.get('Instance0',{}).get('SaveFilePath',''))
            if folder and not Path(folder).is_absolute():folder=str((self.runtime/folder).resolve())
            self.owner.save_dir.set(folder);self.owner._active_profile()['save_dir']=folder;self.owner._save()
            self.status.set('Settings saved. Backup: melonDS.toml.before-all-settings. Changes apply next launch.')
        except (OSError,ValueError) as exc:self.status.set(str(exc))
