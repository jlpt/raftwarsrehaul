#!/bin/bash
# Build windows/RobokillMod.exe: Ruffle (winbuild/ruffle, patched in desktop/src/robokill.rs)
# with robokill_mod.swf baked in, cross-compiled for 64-bit Windows using llvm-mingw.
# Run ./build.sh first if you changed the mod; this picks up the current robokill_mod.swf.
set -e
cd "$(dirname "$0")"
toolchain=$(echo "$PWD"/toolchain/llvm-mingw-*/bin)
# Java (the JRE bundled for JPEXS) is needed by Ruffle's build to compile its playerglobal library.
java_dir=$PWD/../tools/jre/bin; [ -x "$java_dir/java" ] || java_dir=$(dirname "$(command -v java)")
export PATH="$toolchain:$java_dir:$PATH"
export CARGO_TARGET_X86_64_PC_WINDOWS_GNULLVM_LINKER=x86_64-w64-mingw32-clang
# Link libunwind statically so the exe doesn't need any DLLs from llvm-mingw.
export CARGO_TARGET_X86_64_PC_WINDOWS_GNULLVM_RUSTFLAGS="-C target-feature=+crt-static"
(cd ruffle && cargo build --profile dist --target x86_64-pc-windows-gnullvm -p ruffle_desktop)
mkdir -p ../windows
cp ruffle/target/x86_64-pc-windows-gnullvm/dist/ruffle_desktop.exe ../windows/RobokillMod.exe
cp ruffle/LICENSE.md ../windows/Ruffle-LICENSE.md
echo "Built $(cd ../windows && pwd)/RobokillMod.exe"
