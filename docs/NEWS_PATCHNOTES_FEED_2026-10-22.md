# Launcher News feed check — 2026-10-22

The 2.0.27 release notes were present on the release branch and on the GitHub Release, but the installed launcher reads `patchnotes/index.json` from `main`. That default-branch index still ended at 2.0.26, so the News page did too.

The 2.0.27 note, index entry, and README link were added to `main`. Both bundled `news.json` copies were synchronized, and the patch-note test now allows the default branch to show notes newer than its source `VERSION.txt` while still requiring the checked-out version's note and descending order. The reusable rule is in [`skills.md` → Launcher News and patch notes](../skills.md#launcher-news-and-patch-notes).

## Verification

- `python -m unittest test_patchnotes_feed -v` — **PASS**, Python 3.14.7, against the 2.0.27 release source at commit `4ea1a657fc705edd34d56a7f17ab945d955660a5` plus the adjusted test assertion.
- `python check_launcher_tree_parity.py` — **PASS**, 43 launcher UI files matched.
- GitHub Contents API confirmed that `main/patchnotes/index.json` starts with 2.0.27 and the 2.0.27 note file exists.
- The first live fetch from `raw.githubusercontent.com` still returned 2.0.26 with `Cache-Control: max-age=300`, despite the Contents API showing the new commit. Recheck the launcher feed after that cache expires; no live launcher UI check has been run.
