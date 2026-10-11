#!/bin/bash
# Perk test on the virtual display (needs build/robokill_debug.swf): Mission 1, then three rounds of
# "equip the next four uniques (J), spawn enemies (K), shoot them" with a screenshot mid-fight
# (build/perk_1..3.png). Prints how often each perk triggered; fails on ActionScript errors.
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
log=build/perk.log
pkill -x ruffle || true
(timeout 400 tools/ruffle/ruffle --save-directory "$tmp/saves" "$swf" > "$log" 2>&1 &)
x() { python3 -I modtools/xinput.py "$@" > /dev/null; }
sleep 9
x move 400 320; x focus
x click 735 560; sleep 3
x click 455 270; sleep 3
x click 400 320
for k in t e s t; do x key $k; sleep 0.2; done
x click 380 403; sleep 4
x click 110 316; sleep 6                          # MISSION 1
x click 290 182; sleep 3                          # SKIP briefing
for round in 1 2 3; do
    x key j; sleep 0.5; x key k; sleep 1
    x hold 630 322 2500
    modtools/vshot.sh perk_$round
    x hold 640 300 3500
    sleep 1
done
pkill -x ruffle || true
rm -rf "$tmp"
grep -a "WEAPON debug equip" "$log" | sed 's/.*WEAPON/WEAPON/' || true
for p in crit burn chain siphon volatile spawned; do
    echo "$p: $(grep -ac "PERK $p" "$log")"
done
if grep -aE 'Error dispatching|TypeError|ReferenceError|Error #' "$log"; then
    echo "FAIL: ActionScript errors, see $log"
    exit 1
fi
echo "OK: build/perk_1.png build/perk_2.png build/perk_3.png"
