#!/bin/bash
# Perk test (needs build/robokill_debug.swf): Mission 1 in god mode, then three rounds of "equip the next
# four uniques (J), spawn enemies (K), shoot them" with a screenshot mid-fight (build/perk_1..3.png).
# Prints how often each perk triggered; fails on ActionScript errors.
set -e
cd "$(dirname "$0")/.."
. modtools/game.sh
game_start "${1:-build/robokill_debug.swf}" build/perk.log
game_mission 110 316                              # MISSION 1
x key z                                           # god mode
for round in 1 2 3; do
    x key j; sleep 0.5; x key k; sleep 1
    x hold 630 322 2500
    modtools/vshot.sh perk_$round
    x hold 640 300 3500
    sleep 1
done
game_end
grep -a "WEAPON debug equip" build/perk.log | sed 's/.*WEAPON/WEAPON/' || true
for p in crit burn chain siphon volatile spawned; do
    echo "$p: $(grep -ac "PERK $p" build/perk.log)"
done
echo "OK: build/perk_1.png build/perk_2.png build/perk_3.png"
