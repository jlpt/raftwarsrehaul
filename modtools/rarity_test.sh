#!/bin/bash
# Weapon rarity test on the virtual display (needs build/robokill_debug.swf from modtools/build_debug.sh).
# Mission 1: drops one weapon of each rarity (G x6) -> build/rarity_drops.png, equips four uniques (J) and
# shoots -> build/rarity_fire.png, opens the inventory -> build/rarity_inv.png and hovers two weapons
# (build/rarity_tip_*.png). Fails on ActionScript errors.
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
log=build/rarity.log
pkill -x ruffle || true
(timeout 400 tools/ruffle/ruffle --save-directory "$tmp/saves" "$swf" > "$log" 2>&1 &)
x() { python3 -I modtools/xinput.py "$@" > /dev/null; }
sleep 9
x move 400 320; x focus
x click 735 560; sleep 3                          # skip intro
x click 455 270; sleep 3                          # START
x click 400 320
for k in t e s t; do x key $k; sleep 0.2; done
x click 380 403; sleep 4                          # CONTINUE -> mission select
x click 110 316; sleep 6                          # MISSION 1
x click 290 182; sleep 3                          # SKIP briefing
x move 650 450
for _ in 1 2 3 4 5 6; do x key g; sleep 0.6; done
sleep 1; modtools/vshot.sh rarity_drops
x key j; sleep 1
x key l; sleep 0.5                                # save round trip of the equipped weapons
x hold 700 150 2500
modtools/vshot.sh rarity_fire
x click 729 618; sleep 2                          # INV button
modtools/vshot.sh rarity_inv
x move 213 369; sleep 1; modtools/vshot.sh rarity_tip_legendary   # top-left weapon slot
x move 335 459; sleep 1; modtools/vshot.sh rarity_tip_mythic      # bottom-right weapon slot
pkill -x ruffle || true
rm -rf "$tmp"
grep -a "WEAPON\|SAVE" "$log" | sed 's/.*\(WEAPON\|SAVE\)/\1/' || true
if grep -aq "SAVE MISMATCH" "$log"; then echo "FAIL: weapon changed in the save round trip"; exit 1; fi
if grep -E 'Error dispatching|TypeError|ReferenceError|Error #' "$log"; then
    echo "FAIL: ActionScript errors, see $log"
    exit 1
fi
echo "OK: build/rarity_drops.png build/rarity_fire.png build/rarity_inv.png"
