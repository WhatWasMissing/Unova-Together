"""Verify that editor auditing detects unintended code and growth changes."""
import copy
from pathlib import Path
import struct
import tempfile

import ndspy.fnt
import ndspy.narc
import ndspy.rom
from audit_gen5_editor_export import audit


def main():
    rom = ndspy.rom.NintendoDSRom()
    rom.idCode = b'IREO'
    narc = ndspy.narc.NARC()
    narc.files = [struct.pack('<101I', *[i ** 3 for i in range(101)]) for _ in range(6)]
    rom.files = [narc.save()]
    leaf = ndspy.fnt.Folder(files=['7'])
    rom.filenames = ndspy.fnt.Folder(folders=[('a', ndspy.fnt.Folder(folders=[
        ('0', ndspy.fnt.Folder(folders=[('1', leaf)]))]))])
    with tempfile.TemporaryDirectory(prefix='unova-editor-audit-') as folder:
        original, edited = Path(folder) / 'before.nds', Path(folder) / 'after.nds'
        original.write_bytes(rom.save())
        edited.write_bytes(rom.save())
        assert audit(original, edited)['contentUnchanged']
        changed = copy.deepcopy(rom)
        changed.arm9 = b'changed code'
        edited.write_bytes(changed.save())
        result = audit(original, edited)
        assert not result['contentUnchanged'] and not result['arm9Unchanged']
        changed = copy.deepcopy(rom)
        entry = bytearray(narc.files[3])
        struct.pack_into('<I', entry, 20 * 4, 9999)
        altered = copy.deepcopy(narc)
        altered.files[3] = entry
        changed.files[0] = altered.save()
        edited.write_bytes(changed.save())
        result = audit(original, edited)
        assert not result['contentUnchanged'] and not result['growthTablesUnchanged']
        assert result['changedFiles'][0]['changedEntries'] == [3]
        changed = copy.deepcopy(rom)
        changed.idCode = b'IRDO'
        edited.write_bytes(changed.save())
        assert not audit(original, edited)['contentUnchanged']
    print('Editor audit: unchanged content accepted; code, growth entry and ROM identity changes rejected')


if __name__ == '__main__':
    main()
