"""Verify imported cutouts against local source pixels and preserved BTX hashes.

Unova Together: Copyright (C) 2026 mvq1303. GPL-3.0-or-later.
"""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sheets',type=Path,required=True)
    args=parser.parse_args()
    assets=ROOT/'assets/followers'; folder=assets/'official-hgss'
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    sheets={}
    for source in manifest['sheets']:
        path=args.sheets/source['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:
            raise AssertionError('Source sheet hash mismatch: '+path.name)
        sheets[path.name]=Image.open(path).convert('RGB')
    bases={v['species'] for v in manifest['variants'] if v['form']==0 and v['gender']==2}
    if bases!=set(range(1,494)): raise AssertionError('Base species coverage differs')
    keys=set();poses=0
    for variant in manifest['variants']:
        key=(variant['species'],variant['form'],variant['gender'])
        if key in keys: raise AssertionError('Duplicate variant')
        keys.add(key)
        path=folder/variant['asset']; data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=variant['sha256']: raise AssertionError('Asset hash mismatch')
        atlas=Image.open(path).convert('RGBA');size=variant['frameSize']
        if atlas.size!=(size,size*variant['frames']): raise AssertionError('Atlas dimensions differ')
        for i,pose in enumerate(variant['poses']):
            sheet=sheets[pose['sheet']];x,y,w,h=pose['rect'];left,top,right,bottom=pose['visibleBounds']
            if x<0 or y<0 or x+w>sheet.width or y+h>sheet.height: raise AssertionError('Crop escapes source')
            frame=atlas.crop((0,i*size,size,(i+1)*size)); box=frame.getbbox()
            if box is None or box[2]-box[0]!=right-left or box[3]-box[1]!=bottom-top:
                raise AssertionError('Opaque geometry mismatch')
            visible=frame.crop(box);reference=sheet.crop((x+left,y+top,x+right,y+bottom))
            for color,original in zip(visible.get_flattened_data(),reference.get_flattened_data()):
                if color[3] not in (0,255): raise AssertionError('Smoothed alpha detected')
                if color[3] and color[:3]!=original: raise AssertionError('Source pixel changed')
            poses+=1
    original=json.loads((assets/'variants/manifest.json').read_text(encoding='utf-8'))
    for variant in original['variants']:
        path=assets/'variants'/variant['asset']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=variant['sha256']:
            raise AssertionError('Original normal/shiny BTX changed: '+path.name)
    print(f'PASS: {len(keys)} variants, {poses} pixel-exact source cutouts, all 493 base species; all {len(original["variants"])} original BTX files unchanged.')

if __name__=='__main__':main()
