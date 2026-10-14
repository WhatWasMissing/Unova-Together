# Headless NSBMD writer

Source: https://github.com/Yackerw/Blender-NSBMD (MIT, Yackerw 2025). License retained.

Adaptations: removed the Blender import for binary writing; allow empty texture and palette dictionaries and untextured material indices; write the correct one-block header for model-only output. Blender UI helpers in util.py are unused. The installer creates a single-node, single-material original courtyard with vertex colours, fixes mesh counts, and writes native Black 2 field and collision data.
