# Unova Together 1.0.10 checks

- Author gameplay confirmation: bobbing works, hitching resolved, followers no longer disappear while idle, shiny Audino displays correctly.
- Production shiny-function matching: original threshold 8, Redux threshold 128, XOR boundary values, malformed/ambiguous fallback and actual local game RAM. Private captures are excluded.
- Production polling: 20,000 reads against a stalled core produce only two outstanding requests; no GUI wait; fresh responses and stopped-core behavior checked.
- Encrypted party decoder: 96 cases across all permutations, flags, checksum/busy rejection and read-only behavior.
- Renderer: stable sprite dimensions and opaque pixels throughout idle bobbing; camera, motion and reduced-motion regressions.
- Audino: all 12 normal/shiny directional frames differ with matching geometry; complete follower variants checked.
- Relay: 16 socket/protocol checks including shiny/gender metadata. Current hosted relay verified listening locally.
- Full native Release build and installed-binary startup passed. Release packaging verifies exact binary, matching launcher metadata, portable controls, dependency notices, checksums and private-file exclusion.

Local gameplay verification does not replace broad WAN or every-species testing. Full free-flight Soaring remains unfinished and optional flight features remain experimental.
