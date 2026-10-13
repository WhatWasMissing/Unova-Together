"""Build pinned, credited follower variants; no ROM, save or recoloured guesswork.

Unova Together: mvq1303 / WhatWasMissing, GPL-3.0-or-later.
Maintenance with OpenAI Codex. Artwork retains hg-engine's original credits.
"""
from pathlib import Path
import concurrent.futures, hashlib, json, re, struct, time, urllib.request
from PIL import Image
import ndspy.texture

ROOT=Path(__file__).resolve().parents[1]
COMMIT='5f1c91fb93ee6d78cf54105ecf1ce1933e043dad'
REFERENCE=ROOT/'research/follower-completion-20261010'
SOURCE=ROOT/'melonDS-source-1.1' if (ROOT/'melonDS-source-1.1').is_dir() else ROOT/'source/melonDS'
DEST=SOURCE/'res/followers/variants'
FORMS={
    201:[f'unown_{c}' for c in 'bcdefghijklmnopqrstuvwxyz']+['unown_exclamation','unown_question'],
    351:['castform_sunny','castform_rainy','castform_snowy'],
    386:['deoxys_attack','deoxys_defense','deoxys_speed'],
    412:['burmy_sandy','burmy_trash'],413:['wormadam_sandy','wormadam_trash'],
    421:['cherrim_sunshine'],422:['shellos_east_sea'],423:['gastrodon_east_sea'],
    479:['rotom_heat','rotom_wash','rotom_frost','rotom_fan','rotom_mow'],
    487:['giratina_origin'],492:['shaymin_sky'],
    493:['arceus_'+t for t in ('fighting','flying','poison','ground','rock','bug','ghost','steel','fire','water','grass','electric','psychic','ice','dragon','dark')],
    550:['basculin_blue_striped'],555:['darmanitan_zen_mode'],
    585:['deerling_summer','deerling_autumn','deerling_winter'],
    586:['sawsbuck_summer','sawsbuck_autumn','sawsbuck_winter'],
    641:['tornadus_therian'],642:['thundurus_therian'],645:['landorus_therian'],
    646:['kyurem_white','kyurem_black'],647:['keldeo_resolute'],648:['meloetta_pirouette'],
    649:['genesect_douse_drive','genesect_shock_drive','genesect_burn_drive','genesect_chill_drive'],
}

def build():
    metadata=json.loads((REFERENCE/'hg-engine-tree.json').read_text());assert metadata['sha']==COMMIT
    tree={e['path']:e for e in metadata['tree']}
    names={int(n) if int(n)<=493 else int(n)-50:name.lower() for name,n in re.findall(
        r'^#define SPECIES_(\w+)\s+(\d+)\s*$',(REFERENCE/'hg-species.h').read_text(),re.M)
        if 1<=int(n)<=493 or 544<=int(n)<=699}
    assert set(names)==set(range(1,650))
    variants=[]
    for species,name in sorted(names.items()):
        for form,directory in enumerate([name]+FORMS.get(species,[])):
            assert 'data/graphics/sprites/'+directory+'/overworld.png' in tree,directory
            variants.append((species,form,2,directory,'overworld'))
            for female,prefix in ((directory,'overworld_female'),(directory+'_female','overworld')):
                if 'data/graphics/sprites/'+female+'/'+prefix+'.png' in tree:
                    variants.append((species,form,1,female,prefix));break
    cache=REFERENCE/'verified-assets'
    sources=sorted({f'data/graphics/sprites/{directory}/{prefix}{suffix}'
        for _,_,_,directory,prefix in variants for suffix in ('.png','.json','-tsure_poke0.pal','-tsure_poke1.pal')})
    def fetch(source):
        relative=source.removeprefix('data/graphics/sprites/');path=cache/relative;entry=tree[source]
        if not path.exists():
            for attempt in range(4):
                try:
                    request=urllib.request.Request(f'https://raw.githubusercontent.com/BluRosie/hg-engine/{COMMIT}/{source}',headers={'User-Agent':'Unova-Together-follower-variants'})
                    data=urllib.request.urlopen(request,timeout=25).read(1024*1024+1)
                    assert len(data)<=1024*1024
                    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==entry['sha']
                    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);break
                except Exception:
                    if attempt==3:raise
                    time.sleep(attempt+1)
        data=path.read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==entry['sha'],source
        return {'path':source,'gitBlob':entry['sha'],'sha256':hashlib.sha256(data).hexdigest()}
    print(f'Verifying {len(variants)} directional variants and {len(sources)} source files.',flush=True)
    provenance=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(fetch,p) for p in sources]
        for i,future in enumerate(concurrent.futures.as_completed(futures),1):
            provenance.append(future.result())
            if i%200==0:print(f'Verified {i}/{len(sources)} sources.',flush=True)
    DEST.mkdir(parents=True,exist_ok=True);report=[]
    for species,form,gender,directory,prefix in variants:
        parent=cache/directory;image=Image.open(parent/(prefix+'.png'))
        assert image.mode=='P'
        info=json.loads((parent/(prefix+'.json')).read_text());poses=sorted(info['frames'].items(),key=lambda v:v[1]['frame'])
        assert len(poses) in (6,8)
        btx=ndspy.texture.NSBTX();visible=[]
        for label,pose in poses:
            w,h=pose['width'],pose['height'];assert w in (32,64) and h in (32,64) and pose['format']==3
            pixels=list(image.crop((0,pose['frame']*h,w,(pose['frame']+1)*h)).get_flattened_data())
            assert len(pixels)==w*h and max(pixels)<=15 and any(pixels)
            # Preserve every source pixel and its native dimensions. The renderer
            # handles grounded idle motion, including sheets with repeated poses.
            visible.append(bytes(pixels));packed=bytes(pixels[i]|pixels[i+1]<<4 for i in range(0,len(pixels),2))
            btx.textures.append((label,ndspy.texture.Texture.fromFlags(0,0,False,False,False,False,w,h,ndspy.texture.TextureFormat.I4,True,0,0,packed,b'')))
        for index in (0,1):
            lines=(parent/f'{prefix}-tsure_poke{index}.pal').read_text().splitlines()
            assert lines[:2]==['JASC-PAL','0100'] and 1<=int(lines[2])<=16
            colors=[tuple(map(int,line.split())) for line in lines[3:3+int(lines[2])]]
            assert all(0<=channel<=255 for color in colors for channel in color)
            colors += [(0,0,0)]*(16-len(colors))
            palette=b''.join(struct.pack('<H',(r>>3)|((g>>3)<<5)|((b>>3)<<10)) for r,g,b in colors)
            btx.palettes.append(('normal' if index==0 else 'shiny',ndspy.texture.Palette(0,0,0,palette)))
        data=btx.save();decoded=ndspy.texture.NSBTX(data);assert len(decoded.palettes)==2
        filename=f'{species}-{form}-{gender}.btx';(DEST/filename).write_bytes(data)
        report.append({'species':species,'form':form,'gender':gender,'source':directory+'/'+prefix,'asset':filename,'frames':len(poses),'sha256':hashlib.sha256(data).hexdigest()})
    manifest={'sourceCommit':COMMIT,'baseSpecies':649,'variants':report,'sources':sorted(provenance,key=lambda p:p['path'])}
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    resource=ROOT/'melonDS-source-1.1/res/followers.qrc'
    resource.write_text('<RCC><qresource prefix="/followers">\n'+''.join(f'<file alias="{i}.btx">followers/{i}.btx</file>\n' for i in range(494,650))+''.join(f'<file alias="variants/{p["asset"]}">followers/variants/{p["asset"]}</file>\n' for p in report)+'</qresource></RCC>\n',encoding='utf-8')
    print(f'Built {len(report)} variants: all 649 base species have authored normal/shiny palettes.',flush=True)

if __name__=='__main__':build()
