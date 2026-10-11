#!/bin/bash
# Weapon rarity test (needs build/robokill_debug.swf). Mission 1: drops one weapon of each rarity (G x6)
# -> build/rarity_drops.png, equips four uniques (J), checks the save round trip (L) and shoots ->
# build/rarity_fire.png, opens the inventory -> build/rarity_inv.png and hovers two weapons
# (build/rarity_tip_*.png). Fails on ActionScript errors or a save mismatch.
set -e
cd "$(dirname "$0")/.."
. modtools/game.sh
game_start "${1:-build/robokill_debug.swf}" build/rarity.log
game_mission 110 316                              # MISSION 1
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
game_end
grep -a "WEAPON debug\|SAVE" build/rarity.log | sed 's/.*\(WEAPON\|SAVE\)/\1/' || true
if grep -aq "SAVE MISMATCH" build/rarity.log; then echo "FAIL: weapon changed in the save round trip"; exit 1; fi
echo "OK: build/rarity_drops.png build/rarity_fire.png build/rarity_inv.png"
