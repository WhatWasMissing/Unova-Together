"""Ensure the local presence relay is available before the emulator connects."""
import argparse,json,socket,subprocess,sys,time,os
from pathlib import Path

def ready(port):
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=.5) as sock:
            sock.sendall((json.dumps(dict(type='join',version=1,name='startup-check',room='startup-check'))+'\n').encode())
            msg=json.loads(sock.makefile().readline())
            return msg.get('type')=='welcome' and msg.get('version')==1
    except (OSError,ValueError): return False

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8765)
    port=parser.parse_args().port
    if not 1<=port<=65535: raise ValueError('Invalid relay port')
    if ready(port): return
    root=Path(__file__).resolve().parents[1]
    logs=root/'transfer'; logs.mkdir(exist_ok=True)
    with (logs/'presence-relay.stdout.log').open('ab') as out, (logs/'presence-relay.stderr.log').open('ab') as err:
        subprocess.Popen([sys.executable,str(root/'tools/presence_server.py'),'--host','0.0.0.0','--port',str(port)],cwd=root,
            stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    for _ in range(30):
        if ready(port): return
        time.sleep(.1)
    raise RuntimeError('The local relay could not start; check transfer/presence-relay.stderr.log')
if __name__=='__main__': main()
