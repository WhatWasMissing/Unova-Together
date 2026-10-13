"""Focused XInput navigation for the Unova Together launcher. mvq1303."""
import ctypes,os,time

class Pad(ctypes.Structure):
    _fields_=[('buttons',ctypes.c_ushort),('lt',ctypes.c_ubyte),('rt',ctypes.c_ubyte),('lx',ctypes.c_short),('ly',ctypes.c_short),('rx',ctypes.c_short),('ry',ctypes.c_short)]
class State(ctypes.Structure):
    _fields_=[('packet',ctypes.c_ulong),('pad',Pad)]

def actions(pad):
    result=set()
    for flag,name in ((1,'up'),(2,'down'),(4,'left'),(8,'right'),(0x1000,'accept'),(0x2000,'back'),(0x100,'previous'),(0x200,'next')):
        if pad.buttons&flag:result.add(name)
    if pad.ly>14000:result.add('up')
    if pad.ly<-14000:result.add('down')
    return result

class Controller:
    def __init__(self):
        self.api=None;self.previous=None;self.repeat=0
        if os.name!='nt':return
        for library in ('xinput1_4','xinput9_1_0'):
            try:self.api=ctypes.WinDLL(library);break
            except OSError:pass
        if self.api:
            self.api.XInputGetState.argtypes=[ctypes.c_uint,ctypes.POINTER(State)];self.api.XInputGetState.restype=ctypes.c_ulong
    def poll(self,active):
        if not self.api or not active:self.previous=None;return set()
        state=State()
        if not any(self.api.XInputGetState(i,ctypes.byref(state))==0 for i in range(4)):
            self.previous=None;return set()
        current=actions(state.pad)
        if self.previous is None:self.previous=current;self.repeat=time.monotonic()+.4;return set()
        pressed=current-self.previous
        if current&{'up','down'} and time.monotonic()>self.repeat:
            pressed|=current&{'up','down'};self.repeat=time.monotonic()+.18
        if not current:self.repeat=time.monotonic()+.4
        self.previous=current;return pressed
