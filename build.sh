#!/usr/bin/env bash
# Raft Wars: Rehauled - build script
#
# Downloads the original Raft Wars (2007) SWF, deobfuscates its ActionScript 2
# with JPEXS FFDec, applies the patches in patches/, appends the new mod code in
# src/, and recompiles everything into dist/raftwars_rehauled.swf.
#
# Usage:
#   ./build.sh            full build from scratch (fetch + export + patch + compile)
#   ./build.sh compile    recompile work/mod (use while developing)
#   ./build.sh patches    regenerate patches/ from work/mod vs work/export
#   ./build.sh html       wrap the SWF into dist/raftwars_rehauled.html
#   DEBUG=1 ./build.sh    also include src/debug/*.as (JS test hooks)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
WORK="$ROOT/work"
DIST="$ROOT/dist"
FFDEC_VER="26.3.0"
FFDEC_URL="https://github.com/jindrapetrik/jpexs-decompiler/releases/download/version${FFDEC_VER}/ffdec_${FFDEC_VER}.zip"
SWF_URL="https://archive.org/download/raft-wars/raft-wars.swf"
SWF_SHA1="f158443e7235161dd2c5ffd412e516019c460e89"   # TASVideos "good dump" of raftwars.swf
OUT="$DIST/raftwars_rehauled.swf"

# JAVA_TOOL_OPTIONS chatter breaks nothing but clutters logs
ffdec() { JAVA_TOOL_OPTIONS= java -jar "$WORK/ffdec/ffdec.jar" "$@"; }

fetch() {
  mkdir -p "$WORK"
  if [ ! -f "$WORK/orig.swf" ]; then
    echo ">> downloading original SWF"
    curl -fsSL -o "$WORK/orig.swf" "$SWF_URL"
  fi
  echo "$SWF_SHA1  $WORK/orig.swf" | sha1sum -c --quiet
  if [ ! -f "$WORK/ffdec/ffdec.jar" ]; then
    echo ">> downloading JPEXS FFDec $FFDEC_VER"
    curl -fsSL -o "$WORK/ffdec.zip" "$FFDEC_URL"
    rm -rf "$WORK/ffdec" && mkdir -p "$WORK/ffdec"
    unzip -q "$WORK/ffdec.zip" -d "$WORK/ffdec"
  fi
}

export_scripts() {
  echo ">> exporting deobfuscated scripts"
  rm -rf "$WORK/export"
  ffdec -config autoDeobfuscate=1,autoDeobfuscateIdentifiers=1,deobfuscateAs12RemoveInvalidNamesAssignments=1 \
        -export script "$WORK/export" "$WORK/orig.swf" > "$WORK/export.log" 2>&1
  [ -f "$WORK/export/scripts/frame_4/DoAction.as" ] || { cat "$WORK/export.log"; exit 1; }
  # FFDec writes CRLF; normalise so patches stay small and apply cleanly
  find "$WORK/export/scripts" -name '*.as' -exec sed -i 's/\r$//' {} +
}

# Only the scripts we touch are re-imported; everything else keeps its original bytecode.
apply_patches() {
  echo ">> applying patches"
  rm -rf "$WORK/mod" && mkdir -p "$WORK/mod"
  for p in "$ROOT"/patches/*.patch; do
    # each patch names its files as a/scripts/... b/scripts/...
    grep '^+++ b/' "$p" | sed 's#^+++ b/##; s#\t.*##' | while read -r f; do
      mkdir -p "$WORK/mod/$(dirname "$f")"
      cp "$WORK/export/$f" "$WORK/mod/$f"
    done
  done
  for p in "$ROOT"/patches/*.patch; do
    patch -s -p1 -d "$WORK/mod" < "$p"
  done
}

compile() {
  echo ">> compiling"
  rm -rf "$WORK/build" && mkdir -p "$WORK/build" "$DIST"
  cp -r "$WORK/mod/scripts" "$WORK/build/scripts"
  # New mod code is appended to the main game script (frame 4), after all
  # original definitions, so it can wrap/override them.
  local main="$WORK/build/scripts/frame_4/DoAction.as"
  for f in "$ROOT"/src/*.as; do printf '\n' >> "$main"; cat "$f" >> "$main"; done
  if [ "${DEBUG:-0}" = "1" ]; then
    for f in "$ROOT"/src/debug/*.as; do printf '\n' >> "$main"; cat "$f" >> "$main"; done
  fi
  rm -f "$OUT"
  ffdec -importScript "$WORK/orig.swf" "$OUT.tmp" "$WORK/build/scripts" > "$WORK/compile.log" 2>&1 || true
  if grep -q "SEVERE" "$WORK/compile.log" || [ ! -f "$OUT.tmp" ]; then
    grep -v '^\s*at ' "$WORK/compile.log" | grep -v JAVA_TOOL | head -20
    rm -f "$OUT.tmp"
    echo "!! compile failed"; exit 1
  fi
  mv "$OUT.tmp" "$OUT"
  echo ">> built $OUT ($(stat -c %s "$OUT") bytes)"
}

make_patches() {
  echo ">> regenerating patches/"
  rm -f "$ROOT"/patches/*.patch
  (cd "$WORK" && find mod/scripts -name '*.as' | sort | while read -r f; do
      rel="${f#mod/}"
      name="$(echo "$rel" | sed 's#^scripts/##; s#\.as$##; s#/#_#g')"
      diff -u --label "a/$rel" --label "b/$rel" "export/$rel" "mod/$rel" > "$ROOT/patches/$name.patch" || true
      [ -s "$ROOT/patches/$name.patch" ] || rm -f "$ROOT/patches/$name.patch"
  done)
  ls "$ROOT/patches"
}

# Self-contained HTML player: the SWF is embedded as base64 and run by Ruffle
# (Flash emulator, loaded from a CDN), so the file works by double-clicking it.
make_html() {
  local html="$DIST/raftwars_rehauled.html"
  [ -f "$OUT" ] || { echo "!! build the SWF first"; exit 1; }
  {
    cat "$ROOT/player/head.html"
    printf 'const SWF_B64 = "'
    base64 -w0 "$OUT"
    printf '";\n'
    cat "$ROOT/player/tail.html"
  } > "$html"
  echo ">> built $html ($(stat -c %s "$html") bytes)"
}

case "${1:-all}" in
  all)      fetch; export_scripts; apply_patches; compile; make_html ;;
  compile)  fetch; compile ;;
  html)     make_html ;;
  patches)  make_patches ;;
  *) echo "unknown command $1"; exit 1 ;;
esac
