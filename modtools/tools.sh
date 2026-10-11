# Sourced by the build scripts: makes sure JPEXS (pinned version) is in tools/ and defines ffdec().
# The pinned version matters: patches/ are diffs against this version's decompile of the original.
FFDEC_VER=26.3.0
FFDEC_DIR=tools/ffdec-$FFDEC_VER
if [ ! -f "$FFDEC_DIR/ffdec-cli.jar" ]; then
  echo ">> downloading JPEXS FFDec $FFDEC_VER into $FFDEC_DIR"
  mkdir -p "$FFDEC_DIR"
  curl -fsSL -o "$FFDEC_DIR.zip" \
    "https://github.com/jindrapetrik/jpexs-decompiler/releases/download/version$FFDEC_VER/ffdec_$FFDEC_VER.zip"
  unzip -q -o "$FFDEC_DIR.zip" -d "$FFDEC_DIR" && rm "$FFDEC_DIR.zip"
fi
JAVA=java
[ -x tools/jre/bin/java ] && JAVA=tools/jre/bin/java
command -v "$JAVA" > /dev/null || { echo "Java 11+ is needed (or put a JRE in tools/jre)" >&2; exit 1; }
ffdec() { JAVA_TOOL_OPTIONS= "$JAVA" -jar "$FFDEC_DIR/ffdec-cli.jar" "$@"; }
