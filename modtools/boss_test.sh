#!/bin/bash
# Mission 17 test (needs build/robokill_debug.swf), using the debug menu: god mode, level 51, four
# mythic Titan lasers; NEXT ROOM twice (rooms generated with elite/variant rolls) -> build/boss_room1/2.png;
# GO TO EXIT: the Overlord with a Warden and a Bulwark; KILL ENEMIES (-20% for the boss)
# until it dies, tracing its health and phase -> build/boss_*.png.
set -e
cd "$(dirname "$0")/.."
. modtools/game.sh
game_start "${1:-build/robokill_debug.swf}" build/boss.log
x click 580 535; sleep 3                          # EPISODE 5
game_mission 390 450                              # MISSION 17
x key z; for _ in 1 2 3 4 5; do x key x; sleep 0.3; done
menu() { x key F2; sleep 2; }
btn() { x click $((160 + 240 * ($1 % 3))) $((122 + 46 * ($1 / 3))); sleep 0.4; }
menu; btn 9; for _ in 1 2 3 4 5; do btn 10; done; btn 19   # LEVEL -> titan, RARITY -> mythic, EQUIP X4
modtools/vshot.sh boss_menu
btn 17; sleep 5                                   # NEXT ROOM
modtools/vshot.sh boss_room1
x hold 600 300 3000
menu; btn 12; x click 400 562; sleep 2            # KILL ENEMIES, CLOSE
menu; btn 17; sleep 5                             # NEXT ROOM
modtools/vshot.sh boss_room2
menu; btn 12; x click 400 562; sleep 2
menu; btn 18; sleep 6                             # GO TO EXIT
modtools/vshot.sh boss_arrive
for i in 1 2 3 4 5 6; do
    x key F2; sleep 1.5; x click 160 306; sleep 0.3; x click 400 562; sleep 1   # KILL ENEMIES: boss -20%
    x hold 400 250 3000
    modtools/vshot.sh boss_fight_$i
done
game_end
grep -a "PERK boss\|WEAPON debug" build/boss.log | sed 's/.*\(PERK\|WEAPON\)/\1/' || true
echo "OK: build/boss_*.png"
