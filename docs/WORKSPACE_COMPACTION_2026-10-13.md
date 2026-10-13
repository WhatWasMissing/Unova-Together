# Development workspace audit and compaction

The F: Unova folder is a playable release package, about 350 MB. The C: folder was
the full development workspace: 43.5 GiB in logical file sizes, including 25.2 GiB
of fixtures, 8.5 GiB of build trees and 3.8 GiB of release downloads. Hard-linked
copies increased Explorer's logical total without using separate disk blocks.

Verified cleanup removed historical/generated files and obsolete build stages.
Unique private ROMs, saves, checkpoints, dumps, screenshots and recovery backups
were archived under `F:\pokemon-workspace-archive\2026-10-13`, with SHA-256 records.
The main evidence ZIP is 11.25 GiB and the older build-stage ZIP is 0.51 GiB.
Original filenames map to content-addressed ZIP entries through their manifests.
One archived saved game was restored and its checksum verified successfully.

The main cleanup removed 75,519 files, followed by 26,162 obsolete stage files;
7,708 empty historical folders were removed. C: folder size fell to approximately
6.8 GiB. Measured C: free space increased by roughly 30 GiB. Remaining large groups
are user game files, source/tools, the current developer emulator, and Qt/toolchain
dependencies needed for continued work. Active ROM/save paths were preserved.

Commands: `tools/compact_dev_workspace.py` previews, `--apply` archives and removes,
and `--staging` handles obsolete stage folders. Existing archives are not silently
overwritten. `tools/apply_workspace_compaction.ps1` validates absolute containment,
every ancestor's reparse-point status, source size and timestamp before deletion.
`tools/restore_workspace_evidence.py` restores selected evidence to a new folder.
Detailed private manifests remain local and are excluded from GitHub publication.

Launcher/source release:
https://github.com/WhatWasMissing/Unova-Together/releases/tag/vlauncher-20261013

Pokemon X rebuild starts in `F:\pokemon-x-coop\next`, mirrored in its emulator
checkout. Eighteen lifecycle/framing/adapter tests pass. An owned read-only emulator
smoke captured 86 observations, including 62 valid Route 2 samples; five original
saves/checkpoints retained their hashes. Native atomic snapshots, identified peer
rendering resources and actual cooperative battle hooks remain the next milestones.
