"""Shared native controls and a static C-Gear-inspired insignia."""
from pathlib import Path
import json
import tkinter as tk
from tkinter import ttk

HERE = Path(__file__).resolve().parent
THEME = json.loads((HERE/'theme.json').read_text(encoding='utf-8'))
C = THEME['colors']
F = THEME['fonts']

def label(parent, text='', size=11, bold=False, color=None, bg=None, role='body', **kw):
    return tk.Label(parent, text=text, font=(F[role], size, 'bold' if bold else 'normal'),
                    fg=color or C['text'], bg=bg or C['background'], anchor='w', **kw)

def button(parent, text, command, kind='neutral', **kw):
    primary=kind=='primary';nav=kind=='nav'
    bg=C['primary'] if primary else C['nav'] if nav else C['surface']
    fg=C['surface'] if primary else C['navText'] if nav else C['text']
    return tk.Button(parent, text=text, command=command, font=(F['body'],10 if nav else 11,'bold' if primary else 'normal'),
        bg=bg, fg=fg, activebackground=C['primaryHover'] if primary else C['navHover'] if nav else C['selection'],
        activeforeground=C['surface'] if primary or nav else C['text'],
        relief='flat', bd=0, padx=14, pady=2 if nav else 9, cursor='hand2', takefocus=True,
        highlightthickness=2, highlightbackground=bg, highlightcolor=C['focus'],
        disabledforeground=C['disabledText'], **kw)

def card(parent, background=None):
    return tk.Frame(parent, bg=background or C['surface'], highlightbackground=C['border'],highlightthickness=1,bd=0,relief='flat')

def set_enabled(widget, enabled, kind='neutral'):
    background=C['primary'] if kind=='primary' else C['surface']
    if not enabled:background=C['disabled']
    widget.configure(state='normal' if enabled else 'disabled',bg=background,
                     highlightbackground=background,cursor='hand2' if enabled else 'arrow')

def emblem(parent, size=64, bg=None):
    bg=bg or C['nav'];canvas=tk.Canvas(parent,width=size,height=size,bg=bg,highlightthickness=0,takefocus=False)
    canvas.create_oval(8,8,size-8,size-8,fill=C['surface'],outline=C['border'],width=3)
    canvas.create_arc(8,8,size-8,size-8,start=0,extent=180,fill=C['primary'],outline=C['border'],width=3)
    canvas.create_line(8,size/2,size-8,size/2,fill=C['nav'],width=5)
    canvas.create_oval(size/2-8,size/2-8,size/2+8,size/2+8,fill=C['surface'],outline=C['nav'],width=4)
    return canvas

class ScrollPage(tk.Frame):
    """One scroll owner per page; wheel events stay within that page."""
    def __init__(self,parent):
        super().__init__(parent,bg=C['background'])
        self.canvas=tk.Canvas(self,bg=C['background'],highlightthickness=0,takefocus=False)
        bar=ttk.Scrollbar(self,orient='vertical',command=self.canvas.yview)
        bar.pack(side='right',fill='y');self.canvas.pack(side='left',fill='both',expand=True)
        self.canvas.configure(yscrollcommand=bar.set)
        self.content=tk.Frame(self.canvas,bg=C['background'])
        self.window=self.canvas.create_window(0,0,window=self.content,anchor='nw')
        self.content.bind('<Configure>',lambda _:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.window,width=e.width))
        self.bind('<Map>',lambda _:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
    def wheel(self,event):
        if self.content.winfo_height()>self.canvas.winfo_height():
            self.canvas.yview_scroll(-int(event.delta/120),'units')
