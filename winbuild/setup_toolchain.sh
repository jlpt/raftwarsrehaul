#!/bin/bash
# One-time setup for winbuild/build_windows.sh on Linux: the Ruffle source at the pinned nightly with
# the mod's patch (winbuild/ruffle), the llvm-mingw cross toolchain (winbuild/toolchain) and the Rust
# Windows target. Needs git, curl, rustup and Java; uses about 3 GB once built.
set -e
cd "$(dirname "$0")"
RUFFLE_COMMIT=2edfd97d11897e6cf6301c30cd87e86d774919c1   # nightly 2026-10-10, the same as tools/ruffle
LLVM_MINGW_VER=20260922
LLVM_MINGW=llvm-mingw-$LLVM_MINGW_VER-ucrt-ubuntu-22.04-x86_64
if [ ! -d ruffle/.git ]; then
    echo ">> fetching Ruffle $RUFFLE_COMMIT"
    git init -q ruffle
    git -C ruffle remote add origin https://github.com/ruffle-rs/ruffle.git
    git -C ruffle fetch -q --depth 1 origin "$RUFFLE_COMMIT"
    git -C ruffle checkout -q FETCH_HEAD
    git -C ruffle apply ../robokill-ruffle.patch
fi
if [ ! -d "toolchain/$LLVM_MINGW" ]; then
    echo ">> downloading $LLVM_MINGW"
    mkdir -p toolchain
    curl -fsSL "https://github.com/mstorsjo/llvm-mingw/releases/download/$LLVM_MINGW_VER/$LLVM_MINGW.tar.xz" | tar -xJ -C toolchain
fi
rustup target add x86_64-pc-windows-gnullvm
(cd ruffle && cargo fetch --target x86_64-pc-windows-gnullvm)
echo "Toolchain ready: run winbuild/build_windows.sh (after ./build.sh)"
