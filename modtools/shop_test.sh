#!/bin/bash
# Shop test (needs build/robokill_debug.swf): opens the shop (debug key O) in Mission 13, where every
# rarity can roll, and hovers the first stock slot -> build/shop.png, build/shop_tip.png. Lists the stock.
set -e
cd "$(dirname "$0")/.."
swf=${1:-build/robokill_debug.swf}
mkdir -p build
if [ ! -S /tmp/.X11-unix/X99 ]; then
    (setsid Xvfb :99 -screen 0 1280x960x24 -ac -nolisten tcp > build/xephyr.log 2>&1 &)
    for _ in $(seq 30); do [ -S /tmp/.X11-unix/X99 ] && break; sleep 0.5; done
fi
export DISPLAY=:99
tmp=$(mktemp -d); mkdir -p "$tmp/saves"
log=build/shop.log
pkill -x ruffle || true
(timeout 300 tools/ruffle/ruffle --save-directory "$tmp/saves" "$swf" > "$log" 2>&1 &)
x() { python3 -I modtools/xinput.py "$@" > /dev/null; }
sleep 9
x move 400 320; x focus
x click 735 560; sleep 3
x click 455 270; sleep 3
x click 400 320
for k in t e s t; do x key $k; sleep 0.2; done
x click 380 403; sleep 4
x click 690 421; sleep 8                          # MISSION 13
x click 290 182; sleep 3                          # SKIP briefing
x key o; sleep 2
modtools/vshot.sh shop
pkill -x ruffle || true
rm -rf "$tmp"
grep -a "WEAPON generated" "$log" | sed 's/.*WEAPON/WEAPON/' || true
if grep -aE 'Error dispatching|TypeError|ReferenceError|Error #' "$log"; then
    echo "FAIL: ActionScript errors, see $log"; exit 1
fi
echo "OK: build/shop.png"
