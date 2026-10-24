# Asset permissions and notices for 2.0.36

The dialogue-art example includes `maintenance-tools/assets/dialogue-art/field-guide-source.png`, original artwork generated with OpenAI ImageGen on 2026-10-24. The two user-supplied screenshots served as layout and palette references only; no Pokémon character, game sprite, portrait, or ROM-extracted image was used. The bundled `ART-CREDITS.md` records this provenance and explains the example profile.

The project owner confirmed public-release permission on 2026-10-24 for the HGSS follower PNGs, the Mega sprite source artwork, and the separate Mega Evolution sound cue included in this release. The release retains the source and contributor credits available to the project. These permissions do not place those assets under the emulator's GPL license.

The 545 normal HGSS follower cutouts in `source/melonDS/res/followers/official-hgss/` came from the five user-supplied sheets recorded in [HGSS follower artwork import](HGSS_FOLLOWER_IMPORT.md). The project credits Dragoon / The Spriters Resource, redblueyellow, and PokeTex in [Follower art credits](FOLLOWER_ART_CREDITS.md). Pokémon artwork remains the property of its original owners.

The Mega sprite arrays in `source/melonDS/src/Gen5MegaSpriteAssets.h` and their animation data in `source/melonDS/res/mega_animations.bin` derive from user-provided Mega sprite artwork. The native source retains its in-file provenance comments. The separately embedded `source/melonDS/res/mega-sounds/mega-evolution.mp3` has no original creator or source recorded in the project materials; public redistribution permission was confirmed for this release, and that missing attribution detail is recorded here rather than guessed.

Directional follower artwork under `source/melonDS/res/followers/` includes assets from BluRosie/hg-engine, pinned to commit `5f1c91fb93ee6d78cf54105ecf1ce1933e043dad`. Its reuse terms require a free, credited project with no payments, optional donations, or paywall. Preserve the original `CREDITS.md` and `ASSET_TERMS.md`, also copied to `ASSET_NOTICES/hg-engine/` in the source release. The project's follower credit and terms are also in [Follower artwork source and terms](FOLLOWER_ART_TERMS.md).

The FreeBIOS ARM7/ARM9 replacements are independent implementations and are not Nintendo BIOS dumps. Keep `source/melonDS/freebios/drastic_bios_readme.txt` with them; it contains their redistribution notice. The menu sounds are project-generated synthesized sounds and are documented in the native source.

The source and runtime releases contain no game ROM, user save, real Nintendo firmware dump, or user-generated gameplay capture. Project artwork, audio, and independent BIOS replacements are included; the emulator's code license does not replace their separate notices and terms.


## FreeBIOS binary redistribution notice

The bundled ARM7/ARM9 replacement binaries reproduce the complete accompanying notice from `drastic_bios_readme.txt`:

```text
Custom NDS ARM7/ARM9 BIOS replacement
Copyright (c) 2013, Gilead Kutnick
All rights reserved.

Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:

1) Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2) Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

-- Info --

This archive contains source code and assembly for a custom BIOS replacement
for the Nintendo DS system. This code is in no way affiliated with Nintendo
and is not derived from Nintendo's BIOS implementation but has been implemented
using publically available documentation.

It can be assembled using the included Makefile along with a proper ARM gcc
toolchain. Change the first four lines to point to the proper toolchain of your
choice.
```

The 2.0.36 release carries forward the previously credited art, audio, and independent FreeBIOS assets. It adds no new game-derived art or user gameplay captures.
