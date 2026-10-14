# 1.0.14 release checks

- Windows x64 native emulator rebuilt from the matching source with version metadata 1.0.14.
- Launcher and emulator metadata agree on release 1.0.14.
- Runtime and source archives pass ZIP integrity, version metadata, checksum and private-file exclusion checks.
- The LAN event-service batch is bounded to four events per worker poll; live hosted-session testing remains for players to verify after download.
- Temporary package staging and build work directories are removed after verification; published release artifacts are retained.
