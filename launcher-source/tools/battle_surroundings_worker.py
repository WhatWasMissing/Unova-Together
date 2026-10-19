"""Asynchronous local scene generation; never runs inside the emulator frame."""
from pathlib import Path
import hashlib
import json
import os
import threading
import uuid
import struct
import time
import ndspy.rom
from build_battle_surroundings import FieldSource, export

REVISION=3


def scene_key(zone,x,z,y):
    return f'{zone}-{int(x//32)}-{int(z//32)}-{round(y)}'


def atomic_json(path,value):
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temporary.write_text(json.dumps(value));os.replace(temporary,path)


class SurroundingsWorker:
    def __init__(self,rom,directory,budget=16384):
        self.rom=Path(rom).resolve();self.directory=Path(directory).resolve()
        self.directory.mkdir(parents=True,exist_ok=True)
        self.stop=threading.Event();self.budget=budget
        self.started=time.time()
        self.thread=threading.Thread(target=self.run,name='Nearby battle scenery',daemon=True)
        self.thread.start()

    def run(self):
        source=None;handled={}
        while not self.stop.wait(.2):
            for request in self.directory.glob('request-*.json'):
                key=None
                try:
                    if request.stat().st_mtime<self.started or request.stat().st_size>4096:continue
                    data=json.loads(request.read_text())
                    if not isinstance(data,dict):raise ValueError('Invalid scene request')
                    zone=data['zone'];x=data['worldX'];z=data['worldZ'];y=data['worldY']
                    if type(zone) is not int or not 0<=zone<4096:raise ValueError('Invalid zone')
                    if not all(type(v) in (int,float) and -32768<=v<=131072 for v in (x,y,z)):raise ValueError('Invalid position')
                    key=scene_key(zone,x,z,y)
                    if data.get('key')!=key:raise ValueError('Invalid scene key')
                    if handled.get(request)==key:continue
                    if source is None:source=FieldSource(ndspy.rom.NintendoDSRom.fromFile(str(self.rom)))
                    destination=self.directory/f'scene-v{REVISION}-{key}'
                    report_path=destination/'scene.json'
                    if not report_path.is_file():
                        temporary=self.directory/('pending-'+uuid.uuid4().hex)
                        report=export(source,zone,x,z,y,temporary,self.budget)
                        report.pop('geometry',None)
                        (temporary/'scene.json').write_text(json.dumps(report))
                        os.replace(temporary,destination)
                    else:report=json.loads(report_path.read_text())
                    if not isinstance(report,dict):raise ValueError('Invalid nearby scene cache')
                    model_name=report.get('model');model_size=report.get('bytes');model_hash=report.get('sha256')
                    omitted=report.get('omittedProps',[])
                    if (model_name!='surroundings.nsbmd' or type(model_size) is not int or model_size<0 or
                            not isinstance(model_hash,str) or len(model_hash)!=64 or
                            any(character not in '0123456789abcdef' for character in model_hash) or
                            not isinstance(omitted,list)):
                        raise ValueError('Invalid nearby scene cache')
                    model=destination/model_name
                    if model.stat().st_size!=model_size or hashlib.sha256(model.read_bytes()).hexdigest()!=model_hash:
                        raise ValueError('Invalid nearby scene cache')
                    result={'key':key,'model':str(model.relative_to(self.directory.parent)),
                            'sha256':model_hash,'bytes':model_size,'zone':zone,
                            'omittedProps':len(omitted)}
                    atomic_json(request.with_name(request.name.replace('request-','ready-')),result)
                    handled[request]=key
                except (OSError,ValueError,KeyError,IndexError,AssertionError,struct.error) as error:
                    if key is not None:
                        try:
                            atomic_json(request.with_name(request.name.replace('request-','ready-')),{'key':key,'fallback':str(error)[:180]})
                        except OSError:
                            continue
                    handled[request]=key
