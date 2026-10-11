# Robokill mod: guide for agents

A mod of the Flash game **Robokill: Titan Prime** (AS3/Flex SWF, 800×600). It adds enemy tiers 4–6,
Episode 5 (missions 14–17), and 240 fps rendering with interpolation. It ships two ways:

- `robokill_mod.swf`: play it with `./play.sh` (bundled Linux Ruffle) or any Ruffle.
- `windows/RobokillMod.exe`: Ruffle for Windows with the SWF built in. It starts fullscreen.

`README.md` is the player-facing summary. `docs/MODDING.md` covers the engine, data formats and recipes.
Read it before making non-trivial changes.

## Layout

**The repository is public and holds no original game code.** `original/`, `decompiled/`, `mod_src/`,
`tools/` and every SWF/exe are gitignored. Mod changes are committed as `patches/` (unified diffs against
the JPEXS decompile); `build.sh` turns them back into `mod_src/`.

| Path | What | In git |
|---|---|---|
| `original/robokill.swf` | Untouched original game (Miniclip build, sha1 `0893aa0a…`). Every build starts from this. | no: copy it in |
| `decompiled/scripts/` | JPEXS decompile of the original (made by `build.sh`), for reference only. Never edit. | no |
| `mod_src/` | Modified classes, the editable working copy. Each `.as` file replaces the class of the same name. | no |
| `patches/` | One diff per modified class (`patches/<pkg>/<Class>.as.patch`). What gets committed. | yes |
| `modtools/` | Build helpers, mission generator, level-data tools, test helpers (input, screenshots). | yes |
| `build.sh` | Builds `robokill_mod.swf`. | yes |
| `modtools/build_debug.sh` | Builds `build/robokill_debug.swf`: random tiers 0–6 in missions 14–17. (All builds have every mission unlocked.) | yes |
| `winbuild/` | Windows exe build: `build_windows.sh` and `robokill-ruffle.patch`. The Ruffle checkout (`winbuild/ruffle`) and llvm-mingw (`winbuild/toolchain`) are local only. | script + patch |
| `windows/` | Build output: `RobokillMod.exe` and Ruffle's licence. | no |
| `tools/` | `ffdec-26.3.0` (JPEXS, downloaded by the build), optional `jre` (else system Java), `ruffle` (Linux Ruffle, for testing). | no |

## Build commands

```bash
./build.sh                      # decompile (first run), sync patches, regenerate missions, compile robokill_mod.swf
modtools/build_debug.sh         # build/robokill_debug.swf (testing; run ./build.sh first)
winbuild/build_windows.sh       # windows/RobokillMod.exe; run ./build.sh first, the exe embeds the SWF
./play.sh                       # play robokill_mod.swf in tools/ruffle
```

`modtools/compile.sh` (used by both builds) fails the build on any JPEXS line containing `error` or
`exception` and prints it. An incremental exe rebuild takes about 2–3 minutes (LTO link).
`winbuild/ruffle/target` uses about 2 GB.

JPEXS is pinned to 26.3.0 (`modtools/tools.sh`) because `patches/` are diffs against its decompile. Its
export of `original/robokill.swf` is byte-identical to the decompile the mod was first written against.

## How code changes work

1. Copy the class from `decompiled/scripts/<pkg>/<Class>.as` to `mod_src/<pkg>/<Class>.as`.
2. Edit it and mark every change with a `// MOD:` comment. `grep -rn "// MOD" mod_src` then lists all changes.
3. Run `./build.sh`, then run the game and check Ruffle's log (see Testing). The build writes your
   `mod_src/` edits back into `patches/` (`modtools/patches.py sync`). Commit `patches/`.

`patches.py sync` keeps the two in step: if only `mod_src/` changed it rewrites `patches/`; if only
`patches/` changed (after a `git pull`) it rebuilds `mod_src/`; if both changed it stops and tells you to
pick one (`patches.py apply --force` or `patches.py make --force`). The generated mission block in
`LevelGrid.as` is left out of the patch and re-spliced on every build.

Verified pitfalls:
- **Only existing classes can be replaced.** A new class fails with `... is not recognized as a CharacterId
  or a script name`. Put new code and data in an existing class (for example as static members).
- **Line endings don't matter.** `patches.py` diffs LF-normalised text and writes `mod_src/` with CRLF
  (like the JPEXS export); mixed endings in a file you edit are harmless.
- **Helper classes in an existing file work.** A file may define extra non-public classes after the
  `package { }` block (`class Foo { ... }`); JPEXS compiles them into the same script. They can't be
  found by name (`getDefinitionByName`), so anything saved to the profile must stay an existing public class.
- **Not all decompiled code works after recompiling.** A named function expression such as
  `arr.filter(function blah(...) {...})` compiles, but at runtime throws `ReferenceError: Error #1056:
  Cannot create property ...::blah`. Use an anonymous `function(...)`. Any class you copy into `mod_src` is
  recompiled, so test it at runtime even if you changed only one line.
- Decompiled names (`_loc3_`, `param1`) are machine-generated. Match the surrounding style.
- `modtools/build_debug.sh` uses `sed` to patch the exact string `tier = 3 + i;` in `MainScene`. If you
  change that line, update the script; it greps to check its patch applied.
- `build.sh` regenerates `modtools/extra_missions.as` and splices it into `mod_src/LevelGridTools/LevelGrid.as`.
  Change `modtools/gen_missions.py`, not the generated block.

## Engine essentials

- **Fixed-tick logic:** `Main` starts a 10 ms `Timer` that calls `GameSceneStack.update()`. It runs
  fixed 10 ms logic ticks (100/s) based on `getTimer()`, at most 5 per call. Game speed doesn't depend
  on frame rate, but drops if rendering falls below about 20 fps.
- **Sprite positions:** each tick, `GameScene.update()` calls every object's `update()`, then `syncObj()`.
  `syncObj()` is the only place that writes the display object (`obj.x/y/rotation/scale`).
  Move game objects through `basex/basey`, never `obj.x`.
- **240 fps (MOD):** `GameSceneStack` sets `stage.frameRate = TARGET_FPS` (240) and also updates on
  `ENTER_FRAME`. After every update it draws each `GameObject` and `Particle` between its last two tick
  positions (`renderInterpolated`, alpha = leftover ms / 10). Moves over 100 px in one tick snap
  instead of sliding. Settings: `GameSceneStack.TARGET_FPS`, `interpolate`, `smoothMovingSprites`.
  Ruffle's `--frame-rate N` overrides the frame rate.
- **Stage scaling (MOD):** the game's bundled Miniclip code (`com/miniclip/_MiniclipGameManager.as`) sets
  `stage.scaleMode = NO_SCALE` and `align = TOP_LEFT`, which pins the game to the top-left 800×600 of a
  fullscreen or enlarged window (the rest shows the white SWF background). `GameSceneStack.update()`
  switches it back to `SHOW_ALL`, centred, on every update. It also sets `mainSprite.focusRect = false`, so
  Ruffle draws no yellow focus frame. Mouse input uses `event.stageX/Y`, so aiming stays correct when scaled.
- **Saves:** `SharedObject.getLocal("robokill", "/")`. Ruffle stores it as `localhost/robokill.sol`
  (Linux: `~/.local/share/ruffle/SharedObjects/`, Windows: `%LOCALAPPDATA%\ruffle\SharedObjects\`).
  The exe shares saves with any Ruffle on the same PC. **Test with `--save-directory <copy>`** so the user's save stays untouched.

## Where things live

| Change | Where |
|---|---|
| Frame rate, interpolation, sprite smoothing | `mod_src/GameScene/GameSceneStack.as` (constants at the top) |
| Tier colours, health and XP multipliers | `mod_src/ObjectBase/EnemyBase.as` (`toughnessHealthMult`, `toughnessMult`, `extraTierTints`) |
| Tier odds per extra mission | `mod_src/Scenes/MainScene.as`, `extraTierWeights()` |
| Map size, enemy pools, room budget, seed for missions 14–17 | `modtools/gen_missions.py`, `MISSIONS` |
| Briefing text | `mod_src/Objects/CommWindow.as`, `extraBriefings` |
| Floor tint and pit graphic of extra missions | `mod_src/GameLevels/GameLevel.as` (per-episode `ColorTransform`; `Embeds.pit[...]` index array) |
| Episode 5 menu page, unlocks | `mod_src/Scenes/MainMenu.as` (`unlockAllEpisodes = true`: every mission and the ending selectable; menu-only, saves unaffected) |
| Enemy behaviour / sprite and setup | `decompiled/scripts/ObjectBase/<Name>Base.as` / `ObjectConstructors/<Name>_constructor.as` |
| Player weapons and items | `decompiled/scripts/Weapons/` (for example `Blaster.levelDamage`) |
| Original level data | `decompiled/scripts/Levels/` (parsed to `modtools/levels.json` by `parse_levels.py`) |

## Testing on Linux

`modtools/smoke_test.sh [SWF]` does all of the following automatically. It defaults to the debug SWF, uses a
copied save, goes through the menus into Mission 1, walks and fires, writes `build/smoke_{menu,game}.png`,
and fails on any ActionScript error. Run it after every code change. Manual steps:

```bash
Xephyr :99 -screen 1280x960 -ac -br -noreset &                      # virtual display
cp -r ~/.local/share/ruffle/SharedObjects /tmp/saves                # never test on the real save
DISPLAY=:99 tools/ruffle/ruffle --save-directory /tmp/saves build/robokill_debug.swf > /tmp/r.log 2>&1 &
DISPLAY=:99 python3 -I modtools/xinput.py move 400 320; DISPLAY=:99 python3 -I modtools/xinput.py focus
modtools/vshot.sh name                                              # screenshot -> build/name.png
grep -E 'Error dispatching|TypeError|ReferenceError' /tmp/r.log     # must be empty
pkill -x ruffle                                                     # not pkill -f: it matches your own shell
```

Click positions are stage coordinates plus a 22 px menu bar (none with `--no-gui`). This route reaches
gameplay: skip intro (735,560) → START (455,270) → click (400,320), type a name →
CONTINUE (380,403) → MISSION 1 (110,316) → SKIP briefing (290,182). WASD moves; `xinput.py hold X Y MS` fires.

To check scaling, run with a bigger window (`--no-gui --width 1280 --height 720`), or start with `--fullscreen` and
then `python3 -I modtools/xresize.py 1280 960`. Xephyr has no window manager, so this helper does the resizing.
The game must fill the window, centred. The Windows exe under Wine scales correctly in fullscreen (verified).

**Diagnosing a player's display problem:** the exe logs `Robokill display: window WxH (scale factor, fullscreen),
viewport WxH, stage scale mode` on every change, plus its build time at startup. Ask for the newest file in
`%LOCALAPPDATA%\ruffle\log\` and a screenshot.

To measure frames and ticks per second, build a scratch copy of `mod_src` with a `trace()` in
`GameSceneStack.onEnterFrame`. Ruffle logs `trace` output.

Limits of this machine: rendering runs on the CPU (llvmpipe), so missions draw at about 10 fps and the
logic runs at about half speed (the 5-tick cap). That's an environment limit, not a bug. Under Wine (a
portable build such as Kron4ek's Wine-Builds), the Windows exe renders correctly in fullscreen. In
windowed mode the picture is squeezed to 600 px wide, grey and striped. That's not root-caused
(possibly Wine's DPI handling in Xephyr), so have the user confirm visuals on real Windows.
**Don't blame the environment for a visual problem without finding its cause.** The NO_SCALE bug above
showed up in Xephyr and was wrongly dismissed as an environment issue.

## Windows exe (`winbuild/`)

- `winbuild/ruffle`: Ruffle source at nightly 2026-10-10 (commit `2edfd97`), the same version as
  `tools/ruffle`, with patches. All changes are also in `winbuild/robokill-ruffle.patch`; use
  `git apply` on a fresh checkout.
- `desktop/src/robokill.rs`: embeds `robokill_mod.swf` (`include_bytes!`), writes it to
  `%LOCALAPPDATA%\RobokillMod\robokill_mod.swf` when it changes, and sets the window title.
- `main.rs`: with no file argument it plays the built-in SWF, and starts fullscreen unless `--windowed` is passed.
  `app.rs`: Esc doesn't leave fullscreen, because the game uses Esc for pause; F11 or Alt+Enter toggles it.
  `desktop/assets/favicon.ico` and `favicon-32.rgba` hold the robot icon. `desktop/Cargo.toml`
  `[package.metadata.winresource]` holds the exe details. `build.rs` has a MinGW stack-size linker flag fix.
- Toolchain: `winbuild/toolchain/llvm-mingw-20260922-*`, Rust target `x86_64-pc-windows-gnullvm`,
  `+crt-static`. Ruffle's build needs Java (`tools/jre`). The exe must depend only on Windows system DLLs:
  `winbuild/toolchain/llvm-mingw-*/bin/llvm-objdump -p windows/RobokillMod.exe | grep 'DLL Name'`.
- The exe accepts all Ruffle options, for example `--windowed`, `--frame-rate 144`, `-g dx12|vulkan|gl`, or
  a path to another SWF (such as `robokill_debug.swf`) to play that instead of the built-in game.
