"""Import reviewed HGSS sheet cutouts without scaling or inventing shiny art.

Unova Together tooling: Copyright (C) 2026 mvq1303. GPL-3.0-or-later.
Artwork remains credited to its original owners and sheet rippers.
"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from PIL import Image

# Reviewed 32-pixel, two-column/four-row blocks that differ from the cache.
# Coordinates refer to the supplied sheets, not ROM offsets.
BLOCKS = {
    1: {7:(454,0),8:(519,0),15:(0,129),28:(909,129),43:(909,258),50:(389,387),
        53:(584,387),69:(649,516),70:(714,516),71:(779,516),72:(844,516),
        73:(909,516),88:(909,645),92:(195,774),115:(714,903),130:(714,1032),
        134:(0,1161),135:(65,1161)},
    2: {166:(260,129),179:(454,258),187:(260,387),197:(195,516),200:(389,516),
        204:(324,905),207:(519,905),214:(0,1167),215:(130,1167),224:(0,1296),
        225:(65,1296),227:(195,1296),231:(454,1296),232:(519,1296),240:(324,1425),251:(0,1683)},
    3: {252:(0,0),253:(65,0),271:(389,129),318:(65,645),334:(324,774),338:(584,774),
        340:(714,774),350:(519,903),381:(0,1290)},
    4: {389:(130,0),408:(649,129),430:(389,516),456:(65,903),457:(130,903),
        458:(195,903),461:(389,903),466:(0,1032),469:(195,1032),475:(584,1032)},
}
GENDERS = {(154,1):(2,195,0), (214,1):(2,65,1167)}
MARKERS = {(255,0,255),(0,128,255),(255,128,64)}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def cut_block(sheet, x, y):
    # Border colors vary by generation. They only occur outside sprite pixels.
    separator = sheet.getpixel((64,0))
    if sheet.getpixel((x,y))==separator:
        x+=1
    background = sheet.getpixel((x,y))
    if background==separator: raise ValueError(f'Block starts on separator: {x},{y}')
    frames=[]
    for col,row in ((0,0),(0,1),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3)):
        px,py=x+col*32,y+row*32
        rect=(px,py,min(32,sheet.width-px),min(32,sheet.height-py))
        frames.append((rect, background, separator))
    return frames

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sheets',type=Path,required=True)
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--preview',type=Path)
    args=parser.parse_args()
    audit=json.loads(args.audit.read_text(encoding='utf-8'))
    paths={p.name:p for p in args.sheets.glob('*.png')}
    for entry in audit['sheets']:
        if digest(paths[entry['file']])!=entry['sha256']:
            raise ValueError('Sheet changed since audit: '+entry['file'])
    sheets={name:Image.open(path).convert('RGB') for name,path in paths.items()}
    generations={n:next(name for name in sheets if f'({ordinal} Generation' in name)
                 for n,ordinal in enumerate(('1st','2nd','3rd','4th'),1)}
    args.output.mkdir(parents=True,exist_ok=True)
    imported=[]; retained=[]; changed=[]
    for variant in audit['variants']:
        species,form,gender=(variant[k] for k in ('species','form','gender'))
        generation=next(n for n,maximum in ((1,151),(2,251),(3,386),(4,493)) if species<=maximum)
        name=generations[generation]
        matches=[next((m for m in p['matches'] if m['sheet']==name),None) for p in variant['poses']]
        manual=None
        if form==0 and (species,gender) in GENDERS:
            gen,x,y=GENDERS[species,gender]; name=generations[gen]
            manual=cut_block(sheets[name],x,y)
        elif form==0 and gender==2 and species in BLOCKS[generation]:
            manual=cut_block(sheets[name],*BLOCKS[generation][species])
        elif species==492 and form==1:
            manual=cut_block(sheets[name],260,1548)
        elif species==384 and form==0:
            # This rip uses compact, irregular rows rather than 64x64 tiles.
            # First four poses are exact matches; the side poses are reviewed
            # separately. Preserve N/S ordering from the existing native poses.
            sheet=sheets[name]; bg=sheet.getpixel((325,1290))
            manual=[(tuple(m['bounds']),bg,None) for m in matches[:4]]
            manual += [((325,1379,67,42),bg,None),((392,1379,62,42),bg,None),
                       ((325,1421,67,38),bg,None),((392,1421,62,38),bg,None)]
        if manual is None and not all(matches):
            retained.append(variant['asset']);continue
        relative=Path(variant['source'])
        original=Image.open(args.cache/(str(relative)+'.png'))
        metadata=json.loads((args.cache/(str(relative)+'.json')).read_text(encoding='utf-8'))
        poses=sorted(metadata['frames'].values(),key=lambda p:p['frame'])
        size=max(32,original.width,64 if species==384 else 32)
        atlas=Image.new('RGBA',(size,size*len(poses)))
        cuts=[]
        for i,pose in enumerate(poses):
            if manual is None:
                m=matches[i]; rect=m['bounds']; left,top=m['sourceOffset']
                indices=np.asarray(original.crop((left,pose['frame']*pose['height']+top,
                         left+rect[2],pose['frame']*pose['height']+top+rect[3])))
                alpha=indices!=0
            else:
                rect,bg,border=manual[i]
                left,top=0,0
                rgb=np.asarray(sheets[name].crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3])))
                alpha=np.any(rgb!=bg,axis=2)
                if border is not None: alpha &= np.any(rgb!=border,axis=2)
                for marker in MARKERS: alpha &= np.any(rgb!=marker,axis=2)
            crop=sheets[name].crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3])).convert('RGBA')
            crop.putalpha(Image.fromarray((alpha*255).astype('uint8')))
            box=crop.getbbox()
            if box is None: raise ValueError(f'Empty pose: {variant["asset"]}:{i}')
            crop=crop.crop(box)
            if crop.width>size or crop.height>size:
                raise ValueError(f'Cutout too large: {variant["asset"]}:{i}: {crop.size}')
            atlas.alpha_composite(crop,((size-crop.width)//2,size*(i+1)-crop.height))
            cuts.append({'sheet':name,'rect':list(rect),'visibleBounds':list(box)})
        filename=variant['asset'].replace('.btx','.png')
        output=args.output/filename;atlas.save(output,optimize=True)
        imported.append({'species':species,'form':form,'gender':gender,'asset':filename,
                         'sha256':digest(output),'frameSize':size,'frames':len(poses),
                         'source':variant['source'],'poses':cuts,'reviewedBlock':manual is not None})
        if manual is not None:changed.append((variant['source'],atlas.copy(),size))
    manifest={'sheets':audit['sheets'],'policy':'Normal-only overrides; shiny uses the original separate BTX shiny palette. Uncovered forms and species retain existing assets.',
              'variants':imported,'retainedVariants':retained}
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    if args.preview:
        from PIL import ImageDraw
        preview=Image.new('RGB',(8*180,((len(changed)+7)//8)*110),'#eeeeee');draw=ImageDraw.Draw(preview)
        for i,(label,atlas,size) in enumerate(changed):
            x,y=(i%8)*180,(i//8)*110;draw.text((x+2,y+2),label.split('/')[0],fill='black')
            for j in range(8):
                im=atlas.crop((0,j*size,size,(j+1)*size));box=im.getbbox();im=im.crop(box)
                preview.paste(im,(x+(j%4)*44,y+20+(j//4)*44),im)
        args.preview.parent.mkdir(parents=True,exist_ok=True);preview.save(args.preview)
    print(f'Imported {len(imported)} normal variants ({len(changed)} reviewed replacements); retained {len(retained)} uncovered forms. Shiny BTX files untouched.')

if __name__=='__main__':main()
