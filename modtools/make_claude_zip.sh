#!/bin/bash
# Pack what a chat Claude (claude.ai, no shell access) needs to mod the game: docs, the mod's changed
# classes, mod tools, build scripts, and the original game's decompiled code (minus Flex/Miniclip
# libraries and asset stubs). Output: robokill-for-claude.zip. Re-run after changing the mod.
set -e
cd "$(dirname "$0")/.."
python3 -I - <<'EOF'
import glob, os, zipfile

START = """# Start here (for Claude working from this upload)

This is a mod of the Flash game Robokill. Read `CLAUDE.md` first, then `docs/MODDING.md`.

You are working from an upload, so you can't run the builds or the game. The user will:
1. put the files you change into their copy of the project (same paths as in this zip),
2. run `./build.sh` and `winbuild/build_windows.sh`, then play and report back.

So:
- Always give back **complete files** with their full path (for example `mod_src/ObjectBase/EnemyBase.as`).
- Code changes go in `mod_src/`. To change a game class that isn't there yet, copy it from
  `decompiled/scripts/` (the original game, included here) to the same path under `mod_src/` and edit that.
- Mark changes with `// MOD:` comments. Follow the pitfalls in `CLAUDE.md` (only existing classes can be
  replaced, no named inline functions, etc.).
- Ignore the parts of `CLAUDE.md` about running Xephyr/tests yourself; ask the user to test instead.
"""

files = ["CLAUDE.md", "README.md", "docs/MODDING.md", "build.sh", "play.sh",
         "winbuild/build_windows.sh", "winbuild/robokill-ruffle.patch"]
files += sorted(glob.glob("mod_src/**/*.as", recursive=True))
files += sorted(f for f in glob.glob("modtools/*") if os.path.isfile(f))
skip = ("decompiled/scripts/mx/", "decompiled/scripts/com/", "decompiled/scripts/system/",
        "decompiled/scripts/GlobalSetup/Embeds_")
for f in sorted(glob.glob("decompiled/scripts/**/*.as", recursive=True)):
    name = os.path.basename(f)
    if f.startswith(skip) or name.startswith("_") or "$" in name:
        continue
    files.append(f)

with zipfile.ZipFile("robokill-for-claude.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("START_HERE.md", START)
    for f in files:
        z.write(f)
print(f"robokill-for-claude.zip: {len(files) + 1} files, {os.path.getsize('robokill-for-claude.zip') // 1024} KB")
EOF
