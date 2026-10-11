# Sourced by the test scripts: play a SWF in Ruffle on virtual display :99 with a throwaway save.
#   game_start SWF LOG        start Xvfb/Xephyr if needed, start Ruffle, new profile, open mission select
#   game_mission X Y          click a mission button (screen coords, see build/smoke_menu.png) and skip the briefing
#   x ARGS                    modtools/xinput.py (click X Y | hold X Y MS | key NAME [MS] | move X Y)
#   game_end                  stop Ruffle; fails (exit 1) if Ruffle logged an ActionScript error
# Screen coords = stage coords + 22 px (Ruffle's menu bar).
mkdir -p build
x() { python3 -I modtools/xinput.py "$@" > /dev/null; }
game_start() {
    GAME_LOG=$2
    if [ ! -S /tmp/.X11-unix/X99 ]; then
        if command -v Xephyr > /dev/null && [ -n "$DISPLAY" ]; then
            (setsid Xephyr :99 -screen 1280x960 -ac -br -noreset > build/xephyr.log 2>&1 &)
        else
            (setsid Xvfb :99 -screen 0 1280x960x24 -ac -nolisten tcp > build/xephyr.log 2>&1 &)
        fi
        for _ in $(seq 30); do [ -S /tmp/.X11-unix/X99 ] && break; sleep 0.5; done
        [ -S /tmp/.X11-unix/X99 ] || { echo "FAIL: virtual display didn't start"; exit 1; }
        sleep 1
    fi
    export DISPLAY=:99
    GAME_SAVES=$(mktemp -d); mkdir -p "$GAME_SAVES/saves"
    pkill -x ruffle || true
    (timeout 600 tools/ruffle/ruffle --save-directory "$GAME_SAVES/saves" "$1" > "$GAME_LOG" 2>&1 &)
    sleep 9
    x move 400 320; x focus
    x click 735 560; sleep 3                      # skip intro
    x click 455 270; sleep 3                      # START
    x click 400 320                               # name field
    for k in t e s t; do x key $k; sleep 0.2; done
    x click 380 403; sleep 4                      # CONTINUE -> mission select
}
game_mission() {
    x click "$1" "$2"; sleep 7                    # mission button
    x click 290 182; sleep 3                      # SKIP briefing
}
game_end() {
    pkill -x ruffle || true
    rm -rf "$GAME_SAVES"
    if grep -aE 'Error dispatching|TypeError|ReferenceError|Error #' "$GAME_LOG"; then
        echo "FAIL: ActionScript errors, see $GAME_LOG"
        exit 1
    fi
}
