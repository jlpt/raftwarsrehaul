#!/bin/bash
# Gameplay smoke test on a virtual display: modtools/smoke_test.sh [SWF] [extra Ruffle args...]
# Plays SWF (default build/robokill_debug.swf, which has all missions unlocked) in the bundled Ruffle on
# Xephyr :99 using a throwaway copy of the save data: intro -> new profile -> Mission 1 -> walk and shoot.
# Saves build/smoke_menu.png and build/smoke_game.png; fails if Ruffle logged an ActionScript error.
# Clicks assume the default window (800x600 stage under a 22 px menu bar), so don't pass --no-gui/--width.
set -e
cd "$(dirname "$0")/.."
swf=${1:-build/robokill_debug.swf}
shift || true
if ! pgrep -x Xephyr > /dev/null; then
    (setsid Xephyr :99 -screen 1280x960 -ac -br -noreset > build/xephyr.log 2>&1 &)
    for _ in $(seq 30); do [ -S /tmp/.X11-unix/X99 ] && break; sleep 0.5; done
    [ -S /tmp/.X11-unix/X99 ] || { echo "FAIL: Xephyr didn't start, see build/xephyr.log"; tail -5 build/xephyr.log; exit 1; }
    sleep 1
fi
export DISPLAY=:99   # after starting Xephyr, which opens its window on the real display
tmp=$(mktemp -d)
cp -r ~/.local/share/ruffle/SharedObjects "$tmp/saves" 2> /dev/null || mkdir -p "$tmp/saves"
log=build/smoke.log
pkill -x ruffle || true
(timeout 300 tools/ruffle/ruffle --save-directory "$tmp/saves" "$@" "$swf" > "$log" 2>&1 &)
x() { python3 -I modtools/xinput.py "$@" > /dev/null; }
sleep 9
x move 400 320; x focus
x click 735 560; sleep 3                          # skip intro
x click 455 270; sleep 3                          # START
x click 400 320                                   # name field
for k in t e s t; do x key $k; sleep 0.2; done
x click 380 403; sleep 4                          # CONTINUE -> mission select
modtools/vshot.sh smoke_menu
x click 110 316; sleep 6                          # MISSION 1
x click 290 182; sleep 3                          # SKIP briefing
x move 650 450
x key d 1500; x key a 1500; x key s 800; x key w 800
x hold 700 300 2500                               # fire to the right
modtools/vshot.sh smoke_game
pkill -x ruffle || true
rm -rf "$tmp"
if grep -E 'Error dispatching|TypeError|ReferenceError' "$log"; then
    echo "FAIL: ActionScript errors, see $log"
    exit 1
fi
echo "OK: no ActionScript errors. Screenshots: build/smoke_menu.png build/smoke_game.png"
