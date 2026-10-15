# Unova Together 1.0.26 release checks

Verified on 15 October 2026 against the local Black 2 Redux Complete v1.4.1 ROM overlay and this release source:

- CTest: **8/8 passed**, including Mega battle selection, party ability restoration, move ability hooks, co-op packet handling, shop roster/price policy, Redux cartridge overlay, and ability-hook signatures.
- Mega sprite builder tests: **9/9 passed**.
- Full Windows desktop emulator target: **203/203 build steps passed**.
- Release archives: inspect both ZIPs for integrity, expected 49-form source files, Qt Windows platform plugin, required release docs, portable controls, and exclusion of ROMs, saves, RAM dumps, firmware, and build/test output before upload.
- Marts stock all 49 stones across standard shops while staying within the 45-row shop limit; stored item prices are scaled so the displayed price is ₽50,000.

Live playtest scope: Serperior's battle flow, restoration, and party-menu behavior were previously verified by the project owner. The newly expanded forms need individual live testing, and linked two-player Mega battles remain unverified. The GIF conversion currently imports static frames; the native Gen 5 animation format has been researched but full animated playback is not implemented.
