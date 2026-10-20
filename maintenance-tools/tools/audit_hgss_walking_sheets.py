"""Locate existing follower poses in user-supplied HGSS sheets without resampling.

Matches use exact RGB555 colors and the complete opaque silhouette, ignoring
only translation and the sheet's solid background. No artwork is generated.
"""
# Unova Together tooling: Copyright (C) 2026 mvq1303. GPL-3.0-or-later.
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from PIL import Image


class Sheet:
    def __init__(self, path):
        self.path = path
        rgb = np.asarray(Image.open(path).convert('RGB'), dtype=np.uint16)
        self.colors = (rgb[:, :, 0] >> 3) | ((rgb[:, :, 1] >> 3) << 5) | ((rgb[:, :, 2] >> 3) << 10)
        self.counts = np.bincount(self.colors.ravel(), minlength=32768)
        self.positions = {}

    def find(self, pixels, opaque):
        ys, xs = np.nonzero(opaque)
        if not len(xs):
            return []
        left, top, right, bottom = xs.min(), ys.min(), xs.max()+1, ys.max()+1
        pixels = pixels[top:bottom, left:right]
        opaque = opaque[top:bottom, left:right]
        ys, xs = np.nonzero(opaque)
        values = pixels[ys, xs]
        if np.any(self.counts[np.unique(values)] == 0):
            return []
        anchor = int(np.argmin(self.counts[values]))
        color = int(values[anchor])
        if color not in self.positions:
            self.positions[color] = np.nonzero(self.colors == color)
        cy, cx = self.positions[color]
        x, y = cx-xs[anchor], cy-ys[anchor]
        valid = (x >= 0) & (y >= 0) & (x+pixels.shape[1] <= self.colors.shape[1]) & (y+pixels.shape[0] <= self.colors.shape[0])
        x, y = x[valid], y[valid]
        # Sparse rejection first, then compare every pixel and every transparent
        # hole. Subset matches cannot silently select another form or gender.
        for i in np.linspace(0, len(xs)-1, min(20, len(xs)), dtype=int):
            good = self.colors[y+ys[i], x+xs[i]] == values[i]
            x, y = x[good], y[good]
            if not len(x):
                return []
        result = []
        for px, py in zip(x.tolist(), y.tolist()):
            region = self.colors[py:py+pixels.shape[0], px:px+pixels.shape[1]]
            if not np.array_equal(region[opaque], pixels[opaque]):
                continue
            clear = region[~opaque]
            # A true matching cutout has one solid background, including holes
            # between legs/wings. Reject extra artwork rather than cutting it.
            if len(clear) and len(np.unique(clear)) > 1:
                continue
            result.append({'sheet': self.path.name, 'bounds': [px, py, pixels.shape[1], pixels.shape[0]],
                           'sourceOffset': [int(left), int(top)]})
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sheets', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--maximum-species', type=int, default=493)
    args = parser.parse_args()
    sheets = [Sheet(p) for p in sorted(args.sheets.glob('*.png'))]
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    report = []
    for variant in manifest['variants']:
        species = variant['species']
        if species > args.maximum_species:
            continue
        relative = Path(variant['source'])
        source = args.cache / relative
        image = Image.open(source.with_suffix('.png'))
        meta = json.loads(source.with_suffix('.json').read_text(encoding='utf-8'))
        lines = source.with_name(source.name+'-tsure_poke0.pal').read_text(encoding='utf-8').splitlines()
        rgb = np.array([list(map(int, line.split())) for line in lines[3:3+int(lines[2])]], dtype=np.uint16)
        palette = (rgb[:,0] >> 3) | ((rgb[:,1] >> 3) << 5) | ((rgb[:,2] >> 3) << 10)
        generation = 1 if species <= 151 else 2 if species <= 251 else 3 if species <= 386 else 4
        tag = {1:'1st', 2:'2nd', 3:'3rd', 4:'4th'}[generation]
        candidates = [s for s in sheets if tag in s.path.name or 'Miscellaneous' in s.path.name]
        poses = []
        for label, info in sorted(meta['frames'].items(), key=lambda p:p[1]['frame']):
            width, height, frame = info['width'], info['height'], info['frame']
            indices = np.asarray(image.crop((0, frame*height, width, (frame+1)*height)))
            matches = [match for sheet in candidates for match in sheet.find(palette[indices], indices != 0)]
            poses.append({'frame': frame, 'label': label, 'matches': matches})
        report.append({**variant, 'poses': poses, 'allMatched': all(p['matches'] for p in poses)})
        if len(report) % 50 == 0:
            print('Audited',len(report),'variants;',sum(v['allMatched'] for v in report),'exact matches',flush=True)
    output = {'sheets':[{'file':s.path.name,'sha256':hashlib.sha256(s.path.read_bytes()).hexdigest()} for s in sheets],
              'variants':report}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print('Complete:',len(report),'variants;',sum(v['allMatched'] for v in report),'all poses exact')


if __name__ == '__main__':
    main()
