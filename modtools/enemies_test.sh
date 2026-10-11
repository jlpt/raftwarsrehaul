#!/bin/bash
# Enemy test (needs build/robokill_debug.swf), Mission 1 in god mode with four uniques equipped:
# every elite type (R) -> build/enemies_elites.png, shoot them; the debug menu (F2) -> build/enemies_menu.png
# and its KILL ENEMIES button; every variant (B) at tier 3 -> build/enemies_variants.png, shoot; the
# Overlord (C) -> build/enemies_boss*.png. Prints what triggered; fails on ActionScript errors.
set -e
cd "$(dirname "$0")/.."
. modtools/game.sh
game_start "${1:-build/robokill_debug.swf}" build/enemies.log
game_mission 110 316                              # MISSION 1
x key z; x key j; sleep 0.5                       # god mode, four uniques
x key r; sleep 2.5
modtools/vshot.sh enemies_elites
x hold 640 300 5000
modtools/vshot.sh enemies_elites_fight
x key F2; sleep 2
modtools/vshot.sh enemies_menu
x click 160 306; sleep 0.5                        # KILL ENEMIES
x click 400 562; sleep 2                          # CLOSE
for _ in 1 2 3; do x key t; done                  # tier 3
x key b; sleep 4
modtools/vshot.sh enemies_variants
x hold 640 300 5000
modtools/vshot.sh enemies_variants_fight
x key F2; sleep 2; x click 160 306; sleep 0.5; x click 400 562; sleep 2
x key c; sleep 6
modtools/vshot.sh enemies_boss
x hold 640 300 6000
modtools/vshot.sh enemies_boss_fight
sleep 4
modtools/vshot.sh enemies_boss_late
game_end
grep -a "PERK spawned\|PERK boss" build/enemies.log | sed 's/.*PERK/PERK/'
echo "OK: build/enemies_*.png"
