# Modding guide

This guide goes deeper than `CLAUDE.md`: how the game's code is organised, the level-data formats, and
step-by-step recipes. Paths under `decompiled/scripts/` are the original game; anything you change must
be copied into `mod_src/` first (see `CLAUDE.md` → *How code changes work*).

## Build pipeline

```
original/robokill.swf ──JPEXS export──▶ decompiled/scripts/*.as ──copy+edit──▶ mod_src/*.as ◀──sync──▶ patches/*.patch (git)
modtools/gen_missions.py ──▶ extra_missions.as ──splice──▶ mod_src/LevelGridTools/LevelGrid.as
                                                      ▼
original/robokill.swf ──JPEXS -replace (modtools/compile.sh)──▶ robokill_mod.swf ──include_bytes──▶ windows/RobokillMod.exe
                                                                                  (winbuild/build_windows.sh)
```

JPEXS recompiles every class found in `mod_src` from source and swaps it into the original SWF. Every
other class keeps its original bytecode.

## Code map (`decompiled/scripts/`)

| Package | Contents |
|---|---|
| `Main.as` | Entry point. Starts `GameTimer(10)` → `GameSceneStack.update()`. |
| `GameScene/` | `GameSceneStack` (main loop, scene stack, fades), `GameScene` (one screen: objects, cameras, z-order layers), cameras. |
| `GameObject/` | `GameObject` (every sprite/text/button) and `GameObjectFilter*`, small reusable behaviours such as blink, pulse, fade and rotate. |
| `Scenes/` | `MainMenu` (menus, profiles, mission select), `MainScene` (gameplay), `Story*`/`End` (cutscenes). |
| `SceneConstructors/` | Generated layout code that builds each scene's static objects. |
| `ObjectBase/` | Behaviour classes: `PlayerBase`, `EnemyBase`, `BulletBase`, `<Enemy>Base`, bosses… |
| `Objects/` | Concrete classes (`Grunt extends GruntBase`) that tie a behaviour to its sprite/setup. |
| `ObjectConstructors/` | `<Name>_constructor.setup()`: sprite, animation, collision shape and particles for each object type. |
| `Weapons/` | Player weapons and items (`Blaster.levelDamage`, `ItemShield`, …). |
| `InventoryScreen/` | HUD, inventory, shop, level-up, pause menu, help. |
| `GameLevels/GameLevel.as` | Builds a room: floor, walls, pits, doors, floor tint; spawns objects. |
| `LevelGridTools/LevelGrid.as` | Mission maps: which room is where, bounds, room contents. |
| `Levels/` | Original level data: `mainGameLevels` (missions), `decalSet` (room floor layouts), `defaultSet` (object prefabs), `propertiesSet` (room markers). |
| `Particles/` | Particle system (`ParticleLayer` holds `Particle`s, each a `Bitmap`). |
| `Serialization/` | Save data (`StoreObject` → `SharedObject "robokill"`), profiles. |
| `GlobalSetup/Embeds*.as` | Embedded PNG/JPG assets (958 PNGs, 13 JPGs; no vector animations). |
| `Engine/` | Box2D AS3 port (`b2Body`, `b2BroadPhase`, …) for collision and physics. |
| `Tools/` | Input, interpolation helpers, timers, pathfinding. |
| `mx/`, `com/`, `system/` | Flex framework and Miniclip libraries. Not game code. |

### Object lifecycle (per 10 ms tick)

`GameScene.update()`:
1. Updates the cameras (`camX/camY`, screen shake).
2. Calls `update()` on each root object: animation frame, `helper`s, `filters` (each adjusts
   `modifiedx/y/rotation/scale/alpha` for this tick), particle emitters, children, then the subclass's `_update()`.
3. Calls `syncObj()` on each object: computes the final screen position (parent transform, camera,
   handle offset) and writes `obj.x/y/rotation/scale/alpha`. Objects outside the 800 px width are hidden.
4. Updates the particle layers.

Game state lives in `basex/basey/baseRotation/baseScaleX/baseAlpha`; `modified*` is the per-tick result
after filters. To move something, change `basex/basey` (or add a `GameObjectFilter`), never `obj.x`.

### 240 fps rendering (MOD)

`GameSceneStack.update()` now runs `updateTicks()` (the original loop, which also increments the static
`logicTick`) and then `renderInterpolated(elapsedTicks / 10)`. `syncObj()` and `Particle.update()` record
each sprite's screen position and rotation for the previous and current tick. `renderInterpolated` draws
it between the two. `GameSceneStack` also hooks `ENTER_FRAME` and sets `stage.frameRate = TARGET_FPS`,
so every rendered frame gets a fresh in-between position. Rules:
- Objects not synced in the latest tick (paused scenes, hidden, removed) are left as `syncObj` set them.
- A jump over 100 px in one tick (teleport, room change) snaps instead of sliding.
- With `smoothMovingSprites`, moving `Bitmap`s get `smoothing = true`, so upscaled fullscreen sprites
  glide instead of shimmering. Static ones such as floor tiles keep the game's setting.
- The game has no timeline animations (all art is bitmaps), so a higher frame rate never speeds anything up.

### Stage scaling (MOD)

The original SWF embeds Miniclip's portal code. In `com/miniclip/_MiniclipGameManager.onAddedToStage` it sets
`stage.scaleMode = NO_SCALE` and `stage.align = TOP_LEFT`, so in a bigger window or in fullscreen the game
stays 800×600 in the corner and the rest shows the SWF's white background (`SetBackgroundColor #ffffff`).
`GameSceneStack.update()` resets it to `SHOW_ALL` with centred alignment on every update, because the
Miniclip code may run after the first update. Ruffle desktop letterboxes with black by default
(`--letterbox on`). Input uses `MouseEvent.stageX/Y`, which stays in 800×600 stage coordinates when scaled.

## Missions and episodes

`MainScene.currentEpisode` is 0-based: mission *N* is episode *N−1*. The original game has missions
1–13 (episodes 0–12); the mod adds missions 14–17 (episodes 13–16, `LevelGrid.FIRST_EXTRA_EPISODE = 13`,
`MainScene.FINAL_EPISODE = 16`).

### Original level data (`Levels/`, parsed to `modtools/levels.json`)

`modtools/parse_levels.py decompiled/scripts modtools/levels.json` produces:
- `decal[layout] = [[Class, x, y, extra], …]`: a room floor layout. Floor tiles sit on a 52 px grid
  (cell = `((x−36)/52, (y−40)/52)`), plus `FloorProp`s and hazards (`FlameThrowerTile`, `LaserTile`, `Fan`).
- `default[index] = [[Class, …]]`: object prefabs. `gen_missions.py` `OBJ` maps names to indices
  (Grunt=4, Hulk=0, Turret=11, ShopTile=39, KeyPlace=10, …) and asserts that the mapping still holds.
- `missions[episode]["x,y"] = [[set, index, fx, fy], …]`: the rooms of each original mission. `set` is
  `decalSet` (floor layout), `defaultSet` (object at fractional position fx, fy) or `propertiesSet` (markers:
  0 start, 1 key lock, 3 finish, 5 checkpoint, 6 ambush).

### Extra missions (`modtools/gen_missions.py`)

Each entry in `MISSIONS` generates one map: a random-walk main path with side branches, locked treasure
rooms with keys, a key-gated finish room with `guards`, checkpoints, a shop next to the start, and enemies
drawn from `pool` (weights) until each room's threat `budget` (min, max) is spent (costs in `COST`;
enemies in `BIG` need a clear 3×3 area). Only floor layouts used by the original missions are used, so
walls and doors render correctly. Changing `seed` gives a new map with the same settings. Output rooms are
`[gridX, gridY, floorLayout, [markers], [objIndex, fx, fy, …]]` in `LevelGrid.EXTRA_MISSIONS`.
`check_doors.py` and `check_positions.py` check `levels.json` assumptions; `analyze.py` prints statistics.

## Recipes

**Change the frame rate or turn interpolation off.** Edit the constants at the top of
`mod_src/GameScene/GameSceneStack.as`, then `./build.sh`. With `interpolate = false`, the frame rate still
applies, but sprites move only on the 100 Hz ticks. To test a different rate without rebuilding, run Ruffle
or the exe with `--frame-rate N`.

**Tune enemy tiers.** `mod_src/ObjectBase/EnemyBase.as`: `toughnessHealthMult` (health per tier),
`toughnessMult` (XP), `extraTierTints` (colour-matrix tint for tiers 4–5; tier 6 cycles colours).
`levelMult` is a per-episode difficulty multiplier with one entry per episode (17). Tier odds per
extra mission are in `MainScene.extraTierWeights()`, as weights for tiers 3, 4, 5 and 6. Bullet damage
follows the game's own `8 + 6 × tier`.

**Change a weapon.** Copy `decompiled/scripts/Weapons/Blaster.as` (for example) to `mod_src/Weapons/` and
edit `levelDamage` or the other static arrays. Rebuild and fire the weapon in game to check it.

**Add a perk.** Add a `kind` constant to `mod_src/WeaponPlugin/WeaponPluginSplash.as` (before `KIND_COUNT`,
which `WeaponGenerator.applyRarity` uses to build the perk pool), then give it a `roll()` case and an
`attributeText()` label (keep it short: a Mythic's three perks share one 40-character tooltip line).
Implement it where it fires: on hit in `hitEnemy()`, on kill in `WeaponBase.onKill()`, on damage in
`WeaponBase.modifyHitDamage()`, while flying in `BulletBase._update()`, or on firing in `WeaponBase.fire()`.
Read its strength with `wep.perk(kind)`. Add a `trace("PERK …")` behind `WeaponGenerator.debugKeys` and a
line in `modtools/perk_test.sh` so the test counts it.

**Add a unique (legendary/mythic) weapon.** Append an entry to `WeaponGenerator.uniques`: weapon class,
name, one-line effect text, intrinsic perks as `[kind, amount, count]`, and optional `dmg`/`rof`
multipliers or `pierce`. Never reorder or remove entries: saved weapons refer to them by index.

**Tune rarity odds.** `WeaponGenerator.rarityWeights` holds the base odds per source (drop, chest, shop);
`rollRarity()` multiplies Rare and up by `(1 + 0.12 × episode) × (1 + Rare Weapon Sensor % / 50)` to the
power of (rarity − 1); `maxRarity()` caps the rarity by mission. Check with the debug build: every weapon
generated is traced to the log with its rarity.

**Re-roll or resize an extra mission.** Edit its `MISSIONS` entry (`seed`, `rooms`, `main`, `chests`,
`budget`, `pool`, `guards`) and run `./build.sh`. Every mission is selectable from the start, so you can open it directly.

**Add mission 18 (episode 17).** Add a `MISSIONS` entry with `ep=17`, then update each place that is
indexed by episode:
- `MainScene.FINAL_EPISODE`.
- The Episode 5 page layout in `MainMenu`.
- `extraBriefings` in `CommWindow`.
- The tint branch and the pit-index array (`_loc16_`) in `GameLevel`.
- `EnemyBase.levelMult` (append an entry).
- `MainScene.extraTierWeights()`.

To find any others, grep `mod_src` and `decompiled/scripts` for `currentEpisode` and for arrays with
17 entries.

**Change the start-up behaviour of the Windows exe.** Edit `winbuild/ruffle/desktop/src/main.rs` and
`robokill.rs`, run `winbuild/build_windows.sh`, then refresh the saved patch:
`cd winbuild/ruffle && git add -N desktop/src/robokill.rs && git diff --binary > ../robokill-ruffle.patch`.

**Move to a newer Ruffle.** Fetch the new commit into a fresh `winbuild/ruffle`, `git apply ../robokill-ruffle.patch`
(fix any conflicts by hand), rebuild, and also update `tools/ruffle` so the Linux tests use the same
version.

## Testing checklist

1. `./build.sh` (and `modtools/build_debug.sh`) with no `error`/`exception` lines.
2. `modtools/smoke_test.sh` must print `OK`. Look at `build/smoke_menu.png` and `build/smoke_game.png`.
3. If the smoke route doesn't cover your change, play it by hand on the Xephyr display with a copied save
   (commands in `CLAUDE.md`), and grep the Ruffle log for `Error dispatching|TypeError|ReferenceError`.
   For anything visual, also try a scaled window (`--no-gui --width 1280 --height 720`).
4. For timing changes, temporarily `trace()` frames/s and `logicTick`/s from `GameSceneStack.onEnterFrame`
   in a scratch copy of `mod_src`. Expect about 100 ticks/s on real hardware; this machine renders on the
   CPU and only reaches that in menus.
5. For the exe, check `llvm-objdump -p` shows only system DLLs, and that it starts under Wine (if
   available) and writes `AppData/Local/RobokillMod/robokill_mod.swf`. The user has to check visuals on Windows.
