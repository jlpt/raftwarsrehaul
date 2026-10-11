#!/bin/bash
# Build robokill_mod.swf from the original game + this mod.
#
#   original/robokill.swf ──JPEXS──▶ decompiled/scripts ──+ patches/──▶ mod_src/ ──JPEXS -replace──▶ robokill_mod.swf
#
# The original game isn't in git (the repository is public): put your copy at original/robokill.swf.
# First run downloads JPEXS into tools/ and decompiles the game. Edit classes in mod_src/; every build
# writes your edits back to patches/ (what gets committed). See CLAUDE.md.
set -e
cd "$(dirname "$0")"
ORIG_SHA1=0893aa0acc151225504640838839832a480b612a   # Miniclip build, 8753195 bytes
if [ ! -f original/robokill.swf ]; then
  echo "Missing original/robokill.swf: copy the original Robokill SWF there (sha1 $ORIG_SHA1)." >&2
  exit 1
fi
echo "$ORIG_SHA1  original/robokill.swf" | sha1sum -c --quiet - ||
  { echo "original/robokill.swf isn't the expected version (sha1 $ORIG_SHA1)." >&2; exit 1; }
. modtools/tools.sh
if [ ! -f decompiled/scripts/Main.as ]; then
  echo ">> decompiling original/robokill.swf into decompiled/"
  ffdec -export script decompiled original/robokill.swf > /dev/null
fi
[ -f modtools/levels.json ] || python3 -I modtools/parse_levels.py decompiled/scripts modtools/levels.json
python3 -I modtools/patches.py sync
python3 -I modtools/gen_missions.py modtools/levels.json modtools/extra_missions.as
python3 -I modtools/splice_levelgrid.py mod_src/LevelGridTools/LevelGrid.as modtools/levelgrid_extra.as.tmpl modtools/extra_missions.as
modtools/compile.sh mod_src robokill_mod.swf
