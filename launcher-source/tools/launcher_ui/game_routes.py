"""Pokemon Together launch adapters. Existing Unova/DS ownership is unchanged."""
from pathlib import Path
import ipaddress
import subprocess

GAMES={'black2':'Pokemon Black 2 / Redux (Nintendo DS)','pokemon-x':'Pokemon X (3DS research)'}
MODES={'Local two players':'local','LAN host':'host','LAN guest':'guest'}

# Stable mod IDs own navigation; adding a mod never reuses another mod's pages.
MODS={
    'black2':{'name':'Unova Together','game':GAMES['black2'],'platform':'Nintendo DS',
        'description':'Black 2 / Redux',
        'status':'Preview 1.0.7','pages':('Play','Co-op','Features','Profiles','News','Updates','Settings','Tools','Setup')},
    'pokemon-x':{'name':'Pokemon X Together','game':GAMES['pokemon-x'],'platform':'Nintendo 3DS',
        'description':'Exploration and trainer battles',
        'status':'Experimental prototype','pages':('XPlay','XCoop','XGuides')},
}
PAGE_LABELS={'Library':'Mod library','Profiles':'Games & saves','XPlay':'Play','XCoop':'Co-op','XGuides':'Guides'}

def research_command(directory,mode,address='127.0.0.1'):
    root=Path(directory).expanduser().resolve()
    if mode not in ('local','host','guest'):raise ValueError('Unknown 3DS launch mode')
    script=root/'tools'/('start_joinable_session.ps1' if mode=='local' else 'start_lan_coop.ps1')
    if not root.is_dir() or not script.is_file():raise ValueError('Choose the prepared Pokemon X co-op folder containing tools and profiles.')
    if not (root/'profiles/pokemon-x-base.research.json').is_file():raise ValueError('Pokemon X research profile is missing.')
    command=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)]
    if mode=='local':command+=['-GeneralTrainers']
    else:
        command+=['-Role',mode]
        if mode=='host':command+=['-Address','0.0.0.0']
        else:
            try:host=ipaddress.ip_address(address.strip())
            except ValueError:raise ValueError('Enter the room host IPv4 address.') from None
            if host.version!=4 or host.is_unspecified or host.is_multicast:raise ValueError('Enter the room host IPv4 address.')
            command+=['-Address',str(host)]
    return root,command

def launch_research(directory,mode,address='127.0.0.1'):
    root,command=research_command(directory,mode,address)
    result=subprocess.run(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=120)
    if result.returncode:raise ValueError('Pokemon X launcher could not start: '+result.stdout[-1600:].strip())
    return 'Pokemon X co-op started. F9 toggles automatic trainer battles; both players must opt in. Do not save research trials.'
