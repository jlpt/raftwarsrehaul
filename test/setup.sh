#!/usr/bin/env bash
# Fetches the Ruffle web build used by the headless play-test harness (test/run.js).
set -euo pipefail
cd "$(dirname "$0")"
VER=0.7.1
rm -rf ruffle && mkdir -p ruffle
npm pack "@ruffle-rs/ruffle@$VER" >/dev/null
tar xzf "ruffle-rs-ruffle-$VER.tgz" -C ruffle --strip-components=1
rm -f "ruffle-rs-ruffle-$VER.tgz"
echo "ruffle $VER ready in test/ruffle"
