"""Move Unova Together's old notes into patchnotes/ and simplify them."""
from __future__ import annotations

import shutil
from pathlib import Path

from build_patchnotes_index import write_index


NOTES = {
    "0.3.5": ("Easy setup and co-op", """- The launcher can check for updates, host or join a local game, and help you reconnect.
- It now includes setup guides, gameplay screenshots, optional music, and keyboard or controller navigation.
- Updates keep your ROM, saves, and emulator settings. Problem reports stay on your computer until you choose to share them."""),
    "0.3.6": ("Clearer player locations", """- Teammate locations and battle status now recover more reliably after returning to the field.
- The player list gives a clearer message when someone's location cannot be found."""),
    "0.3.7": ("More reliable map tracking", """- Nearby players are matched to the area they are actually visiting.
- Fixed several cases where a teammate's location or battle status could get stuck.
- Teammates can remain visible behind in-game menus when the game camera is available."""),
    "0.3.8": ("Bigger LAN lobbies", """- Local games can now host up to 16 players, and guests can join after the host starts.
- Co-op invitations and reconnects are more reliable.
- Traded Pokémon follow the game's obedience rules in supported Black 2 versions."""),
    "0.3.9": ("Battle scenery and followers", """- Try optional 3D battle scenery made from your own ROM. It is cached on your computer and does not change your game files.
- Pokémon followers now use more accurate sprites and animations.
- Fixed the in-game Options shortcut."""),
    "0.3.10": ("Followers and party stats", """- All 649 original Pokémon now have directional follower sprites.
- Followers have a gentle idle bob, and you can view IVs and EVs in the launcher tools.
- Viewing stats does not change your Pokémon."""),
    "0.3.11": ("Helpful Pokémon tools", """- Browse local encounters by season and relearn level-up moves for free.
- Use field moves while keeping those moves out of your battle move slots. The game still controls whether you can use them."""),
    "0.3.12": ("Simpler menus and co-op tools", """- Pokémon tools, co-op settings, and game options are easier to find.
- Choose solo or co-op trainer battles, start no-reward practice rematches, and challenge another player.
- Show or hide followers and see clearer teammate status messages."""),
    "0.3.13": ("Quicker menus and safer reconnects", """- Switch between Players, Pokémon, Co-op, and Settings from the tabs or with L/R.
- The Options shortcut now opens the right menu, and reconnects recover more cleanly.
- Follower controls and trainer battle settings are easier to find."""),
    "0.4.0": ("Companion interactions and a flight preview", """- Talk to, pet, and play with your lead Pokémon. These interactions are cosmetic and do not change your save.
- Try an experimental flight preview over your current surroundings. The game's normal Fly menu still chooses destinations and landing spots."""),
    "1.0.0": ("The full release", """- Explore together, see teammates, trade items or Pokémon, and battle with friends.
- Includes followers, companion interactions, co-op trainer battles, Pokémon tools, and optional battle scenery.
- The launcher adds profiles, LAN hosting, backups, verified updates, and installation repair."""),
    "1.0.1": ("A reliability update", """- Co-op reconnect and recovery checks have been improved.
- The launcher gives clearer connection information and safer retry options.
- This is mainly a behind-the-scenes maintenance update."""),
    "1.0.2": ("More experience in solo battles", """- Solo battles now give extra experience to help make up for experience not earned while playing co-op.
- Co-op rewards and Pokémon you have already trained are unchanged."""),
    "1.0.3": ("Easier save management", """- Create separate game slots and keep their saves apart.
- Back up or restore saves from one place; the current save is backed up before a restore.
- Added a simple calculator to help plan solo experience."""),
    "1.0.4": ("Safely clean up old installs", """- The launcher can remove unused old game copies to free space.
- It keeps the active game, one rollback copy, and running games. ROMs, saves, backups, and custom files are preserved."""),
    "1.0.5": ("Balanced solo experience", """- The solo experience bonus is now 1.25× instead of 1.65×.
- Existing experience, saves, and co-op rewards are unchanged."""),
    "1.0.6": ("More ways to enjoy your companion", """- Talk to, pet, praise, and play with your lead Pokémon; its reactions reflect its nature and friendship.
- Interactions are just for fun and do not change HP, friendship, items, or saves.
- Hold R and press A while facing your follower, or tap it, to open the menu."""),
    "1.0.7": ("Trainer search and Fly shortcut", """- Search the practice trainer list by name or class before starting a no-reward battle.
- An optional Fly shortcut opens the game's own party menu and destinations."""),
    "1.0.8": ("Launcher updates work more smoothly", """- After an update, the launcher now opens the newly installed version.
- Older shortcuts can follow the newer launcher without changing your saves or settings."""),
    "1.0.9": ("A one-time launcher repair", """- If an older shortcut keeps opening an outdated launcher, run Repair-Launcher.exe once and select the shortcut's original Pokémon Together.exe.
- Close the launcher if Windows asks; the repair never closes the game for you.
- Your ROMs, profiles, saves, and backups stay in place. See the launcher migration guide before running the repair."""),
    "1.0.10": ("Smoother followers", """- Fixed follower hitching and made follower movement smoother.
- A follower stays visible through brief data hiccups and updates correctly when your party or area changes.
- Shiny followers now follow the odds used by the loaded game."""),
    "1.0.13": ("Safer game updates", """- Updates install alongside your current game, so a running game can finish before you switch.
- An unrelated melonDS copy no longer blocks Play or repair.
- Your settings, ROM, and saves stay in place."""),
    "1.0.14": ("Smoother LAN hosting", """- Hosting a local game should feel smoother when several network events arrive together.
- The launcher and emulator now show the same version number. Your ROMs, saves, and settings are kept."""),
    "1.0.15": ("Mega Serperior arrives as a test feature", """- Serperior can Mega Evolve in battle in the supported English Black 2 Redux v1.4.1 game.
- Give it Serperiorite, open Fight, then press L and R together. The Multiplayer Debug tab can grant a test stone.
- This feature is experimental. Save normally before trying it, and use the same version with co-op partners."""),
    "1.0.16": ("More Mega Serperior testing", """- The test now checks Serperior's Mega form and battle stats during a replay.
- A live co-op battle still needs testing. Save normally before trying Mega Evolution."""),
    "1.0.17": ("Mega Serperior battle test", """- The test build adds the custom Mega Serperior form and Serperiorite for the supported Black 2 Redux v1.4.1 game.
- Press L and R together while choosing a move. Use the Debug tab to grant the stone if needed.
- The replay did not cover a complete live battle, so this remains experimental. Save first."""),
    "1.0.18": ("Another Mega Serperior test", """- Mega Serperior remains the only playable Mega in this test build.
- Start a fresh battle with Serperior holding Serperiorite, then press L and R together while choosing a move.
- Earlier testing did not confirm that the battle stays playable afterward. Save normally and treat this as experimental."""),
    "1.0.19": ("Fix for a startup problem", """- Fixed a Windows startup issue that could stop melonDS from opening.
- Close the emulator before updating, then start it again from the launcher.
- Mega Evolution gameplay was not changed in this update."""),
}


def migrate(root: Path) -> None:
    root = Path(root).resolve()
    folder = root / "patchnotes"
    folder.mkdir(exist_ok=True)
    for path in root.glob("RELEASE_NOTES*.md"):
        target = folder / path.name
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite existing patch note: {target}")
        shutil.move(str(path), str(target))
    for version, (title, body) in NOTES.items():
        note = folder / f"RELEASE_NOTES_{version}.md"
        note.write_text(f"# Unova Together {version} — {title}\n\n{body.strip()}\n",
                        encoding="utf-8")
    (folder / "RELEASE_NOTES.md").write_text(
        "# Unova Together release notes\n\n"
        "Browse the notes below to see what changed in each version. "
        "The newest release is listed first in the launcher.\n",
        encoding="utf-8")
    write_index(root)
    if (root / "RELEASE_NOTES.md").exists():
        raise RuntimeError("The old root release-notes file was not moved")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    migrate(args.root)
    print(f"Moved and simplified {len(NOTES)} releases in {args.root / 'patchnotes'}")
