# Generation 5 reference archive

Technical references supplied by the project owner on 2026-10-20, organized for ROM, save, and Pokémon-data research. They supplement the [Generation 5 research index](../../GEN5_RESEARCH_REFERENCES.md); they are not instructions for players or runtime dependencies.

| Reference | Scope |
| --- | --- |
| [B2W2 file system](B2W2_FILE_SYSTEM.md) | Archive paths and historical descriptions |
| [BW PK5 structure](BW_PK5_STRUCTURE.md) | Pokémon records, stats, ribbons, forms, and text encoding |
| [Standard PID creation](STANDARD_PID_CREATION.md) | Annotated historical disassembly trace |
| [B2W2 save layout](B2W2_SAVE_STRUCTURE.md) | Main blocks, checksum copies, downloaded content, and 3DS Link |
| [BW save layout](BW_SAVE_STRUCTURE.md) | Original Black/White blocks and badge-date notes |
| [Local decomp reference](LOCAL_DECOMP.md) | Availability and identification of the newer extracted source |

Original references are credited to **Bond697**, **evandixon**, and the original research contributors as listed on Project Pokémon. User-supplied material is retained with attribution. Unova Together's original contributions remain credited to **mvq1303 / WhatWasMissing**. No ROMs, saves, firmware, or decomp source files are included here.

## Reading the archive

- Black/White and Black 2/White 2 use different layouts. Keep the two save references separate.
- Save-file offsets, ROM archive paths, and runtime addresses describe different address spaces.
- “Mirror” in the save tables names the checksum's copy in the checksum block; it is not the start of an entire backup save.
- Historical unknowns, tentative descriptions, and suspected typos remain visible. Editorial notes identify inconsistencies without silently substituting guessed values.
- Absolute addresses and layouts are not established Redux compatibility evidence. Match the exact supported ROM and decomp routine before using them in code.

The attachments are preserved inside text blocks to retain tabular text, comments, and uncertainty markers. The pasted save tables have been reformatted into Markdown without changing their listed values. No gameplay behavior or save data was changed or tested by this documentation update.
