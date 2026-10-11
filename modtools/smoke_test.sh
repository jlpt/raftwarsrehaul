#!/bin/bash
# Gameplay smoke test on a virtual display: modtools/smoke_test.sh [SWF]
# Plays SWF (default build/robokill_debug.swf) in tools/ruffle on display :99 (Xephyr, or Xvfb when
# headless) with a throwaway save: intro -> new profile -> Mission 1 -> walk and shoot.
# Saves build/smoke_menu.png and build/smoke_game.png; fails if Ruffle logged an ActionScript error.
set -e
cd "$(dirname "$0")/.."
. modtools/game.sh
game_start "${1:-build/robokill_debug.swf}" build/smoke.log
modtools/vshot.sh smoke_menu
game_mission 110 316                              # MISSION 1
x move 650 450
x key d 1500; x key a 1500; x key s 800; x key w 800
x hold 700 300 2500                               # fire to the right
modtools/vshot.sh smoke_game
game_end
echo "OK: no ActionScript errors. Screenshots: build/smoke_menu.png build/smoke_game.png"
