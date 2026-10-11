#!/bin/bash
# New weapon types test (needs build/robokill_debug.swf): in Mission 1, V builds/draws/fires every type at
# every level (TYPECHECK lines), then for each group of four types (N) it spawns enemies (K), shoots and
# screenshots (build/weapons_N.png); L checks the save round trip; the inventory -> build/weapons_inv.png
# and a tooltip -> build/weapons_tip.png. God mode (I) is on throughout.
set -e
cd "$(dirname "$0")/.."
. modtools/game.sh
game_start "${1:-build/robokill_debug.swf}" build/weapons.log
game_mission 110 316                              # MISSION 1
x key i                                           # god mode: the spawned enemies can't end the test
x key v; sleep 4
for round in 1 2 3 4 5; do
    x key n; sleep 0.5; x key l; x key k; sleep 1
    x hold 630 322 1800
    modtools/vshot.sh weapons_$round
    x hold 640 300 2500
done
x key u; sleep 0.5                                # every type into the inventory
x click 729 618; sleep 2                          # INV
modtools/vshot.sh weapons_inv
x move 213 369; sleep 1; modtools/vshot.sh weapons_tip              # top-left weapon slot
game_end
grep -a "TYPECHECK done\|TYPECHECK FAIL\|SAVE MISMATCH" build/weapons.log | sed 's/.*TYPECHECK/TYPECHECK/'
grep -aqE "TYPECHECK done: [1-9][0-9]* ok, 0 failed" build/weapons.log || { echo "FAIL: type check"; exit 1; }
if grep -aq "SAVE MISMATCH" build/weapons.log; then echo "FAIL: save round trip"; exit 1; fi
echo "OK: build/weapons_1..5.png build/weapons_inv.png"
