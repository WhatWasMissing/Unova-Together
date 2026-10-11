"""Compare a Gen 5 editor export with its input, without changing either ROM."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import ndspy.code
import ndspy.narc
import ndspy.rom


def digest(data):
    return hashlib.sha256(data).hexdigest()


def audit(before_path, after_path, frost_path=None):
    before = ndspy.rom.NintendoDSRom.fromFile(str(before_path))
    after = ndspy.rom.NintendoDSRom.fromFile(str(after_path))
    report = {
        'originalSha256': digest(before_path.read_bytes()),
        'exportSha256': digest(after_path.read_bytes()),
        'gameCodeBefore': before.idCode.decode('ascii'),
        'gameCodeAfter': after.idCode.decode('ascii'),
        'fileCountBefore': len(before.files), 'fileCountAfter': len(after.files),
        'arm9Unchanged': before.arm9 == after.arm9,
        'arm7Unchanged': before.arm7 == after.arm7,
        'changedFiles': [], 'changedOverlays': [],
        'gameplayVerified': False,
    }
    for index in range(max(len(before.files), len(after.files))):
        a = before.files[index] if index < len(before.files) else None
        b = after.files[index] if index < len(after.files) else None
        name_a = before.filenames.filenameOf(index) if a is not None else None
        name_b = after.filenames.filenameOf(index) if b is not None else None
        if a == b and name_a == name_b:
            continue
        change = dict(id=index, beforeName=name_a, afterName=name_b,
                      beforeBytes=len(a) if a is not None else None,
                      afterBytes=len(b) if b is not None else None)
        if a is not None and b is not None and a[:4] == b[:4] == b'NARC':
            entries_a, entries_b = ndspy.narc.NARC(a).files, ndspy.narc.NARC(b).files
            change['changedEntries'] = [i for i in range(max(len(entries_a), len(entries_b)))
                                        if i >= len(entries_a) or i >= len(entries_b)
                                        or entries_a[i] != entries_b[i]]
            change['entryDataUnchanged'] = entries_a == entries_b
        report['changedFiles'].append(change)
    for cpu, table in [('arm9', 'arm9OverlayTable'), ('arm7', 'arm7OverlayTable')]:
        oa = ndspy.code.loadOverlayTable(getattr(before, table), lambda oid, fid: before.files[fid])
        ob = ndspy.code.loadOverlayTable(getattr(after, table), lambda oid, fid: after.files[fid])
        for oid in sorted(set(oa) | set(ob)):
            a, b = oa.get(oid), ob.get(oid)
            if a is None or b is None or (a.data, a.ramAddress, a.ramSize, a.bssSize,
                a.staticInitStart, a.staticInitEnd) != (b.data, b.ramAddress, b.ramSize,
                b.bssSize, b.staticInitStart, b.staticInitEnd):
                report['changedOverlays'].append(dict(cpu=cpu, id=oid))
    growth_a = ndspy.narc.NARC(before.getFileByName('a/0/1/7')).files
    growth_b = ndspy.narc.NARC(after.getFileByName('a/0/1/7')).files
    report['growthTablesUnchanged'] = growth_a == growth_b
    if frost_path:
        frost = json.loads(frost_path.read_text(encoding='utf-8-sig'))
        report['frostCurvesMatchOriginal'] = frost.get('xpCurves') == [
            list(struct.unpack('<101I', entry)) for entry in growth_a]
        report['frostTypeNames'] = frost.get('fairyTypeStrings')
        report['fairyAlreadyPresent'] = 'Fairy' in frost.get('fairyTypeStrings', [])
        report['originalUnchangedDuringFrostRun'] = frost.get('originalUnchanged', False)
    report['contentUnchanged'] = (report['gameCodeBefore'] == report['gameCodeAfter']
        and report['arm9Unchanged'] and report['arm7Unchanged']
        and not report['changedOverlays'] and report['growthTablesUnchanged']
        and all(c.get('entryDataUnchanged', False) and c['beforeName'] == c['afterName']
                for c in report['changedFiles']))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('export', type=Path)
    parser.add_argument('--frost-report', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.report.resolve() in {args.original.resolve(), args.export.resolve()}:
        parser.error('Report must not overwrite an input ROM')
    result = audit(args.original, args.export, args.frost_report)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    # Deliberate semantic edits require review; a no-op export must preserve content.
    return 0 if result['contentUnchanged'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
