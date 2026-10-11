#!/bin/bash
# Shop test (needs build/robokill_debug.swf): opens the shop (debug key O) in Mission 13, where every
# rarity can roll -> build/shop.png, then again at player level 51 (debug key P) -> build/shop_late.png,
# and lists the stock it generated.
set -e
cd "$(dirname "$0")/.."
. modtools/game.sh
game_start "${1:-build/robokill_debug.swf}" build/shop.log
game_mission 690 421                              # MISSION 13
x key o; sleep 2
modtools/vshot.sh shop
x click 400 590; sleep 1                          # OK: close the shop
for _ in 1 2 3 4 5; do x key p; sleep 0.3; done   # player level 51
x key o; sleep 2
modtools/vshot.sh shop_late
game_end
grep -a "WEAPON generated" build/shop.log | sed 's/.*WEAPON/WEAPON/' || true
echo "OK: build/shop.png"
