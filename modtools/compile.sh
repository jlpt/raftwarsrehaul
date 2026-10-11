#!/bin/bash
# Compile every class in SRC_DIR into a copy of original/robokill.swf: modtools/compile.sh SRC_DIR OUT_SWF
# Fails if JPEXS reports a compile error. Used by build.sh and modtools/build_debug.sh.
set -e
cd "$(dirname "$0")/.."
src=${1%/}; out=$2
. modtools/tools.sh
args=()
while IFS= read -r f; do
  cls="${f#$src/}"; cls="${cls%.as}"; cls="${cls//\//.}"
  args+=("$cls" "$f")
done < <(find "$src" -name '*.as' | sort)
mkdir -p "$(dirname "$out")"
log=$(mktemp)
if ! ffdec -replace original/robokill.swf "$out" "${args[@]}" > "$log" 2>&1 || grep -qiE 'error|exception' "$log"; then
  grep -v 'EXPERIMENTAL' "$log" | grep -iE -B2 -A8 'error|exception' | head -60
  rm -f "$log" "$out"
  echo "FAILED: compile errors above" >&2
  exit 1
fi
rm -f "$log"
echo "Built $out"
