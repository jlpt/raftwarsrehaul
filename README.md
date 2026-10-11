# Robokill mod: extra tiers, Episode 5, 240 fps

## Play

**Windows:** run `windows/RobokillMod.exe`. It needs no install and no separate Ruffle. It starts fullscreen
at your monitor's resolution.
- **F11** or **Alt+Enter** toggles fullscreen. **Esc** opens the in-game pause menu.
- `RobokillMod.exe --windowed` starts in a window.
- `RobokillMod.exe --frame-rate 144` sets a frame rate other than 240.
- Drag another SWF onto the exe to play it instead, for example `build/robokill_debug.swf`.

**Linux:** `./play.sh` runs `robokill_mod.swf` in the bundled Ruffle.

Every mission is unlocked from the start, including Episode 5 (missions 14–17; use the **EPISODE 5**
button next to BACK on the mission-select screen) and the Ending. Your progress is still saved as
normal. To get the original unlock order back, set `unlockAllEpisodes` to `false` in
`mod_src/Scenes/MainMenu.as` and rebuild. `build/robokill_debug.swf` also gives enemies in missions
14–17 random tiers 0–6, which is handy for testing.

Saves are shared with any Ruffle on the same computer:
- Linux: `~/.local/share/ruffle/SharedObjects/localhost/robokill.sol`
- Windows: `%LOCALAPPDATA%\ruffle\SharedObjects\localhost\robokill.sol`

To move your progress from Linux to Windows, copy that file across.

## What changed
- **240 fps with smooth motion.** The game's logic still runs at its original 100 ticks per second, so
  gameplay speed is unchanged. Every rendered frame draws sprites and particles between their last two
  tick positions. Moving sprites are smoothed, so they glide when upscaled in fullscreen.
- **New enemy tiers** above green → blue → red → yellow:
  4 = purple, 5 = white/silver, 6 = rainbow (colour cycles).
  Health multipliers by tier are 1, 1, 1, 2, 2.75, 3.5, 4.5. XP multipliers are 1, 4, 10, 20, 35, 55, 80.
  Bullet damage keeps the game's own scaling (8 + 6 × tier).
- **Missions 14–17**: new generated maps (30–40 rooms each) with locked treasure rooms, keys,
  a key-gated exit, checkpoints, a mid-mission shop, new briefings and their own floor tints.
  Tier odds: M14 yellow/purple → M15 mostly purple + some white → M16 purple/white + a few rainbow → M17 white/rainbow.
- Finishing Mission 13 still plays the ending. Finishing Mission 17 plays it again.
- **Weapon rarities**: Common, Uncommon, Rare, **Epic**, **Legendary** and **Mythic**. Each has its own
  badge, floor glow (Mythic cycles through the rainbow) and name colour.

  | Rarity | Perks | Damage | First possible in |
  |---|---|---|---|
  | Common | 0 | +0% | Mission 1 |
  | Uncommon | 1 | +5% | Mission 2 |
  | Rare | 2 | +10% | Mission 3 (chests: always Rare or better) |
  | Epic | 3 | +20% | Mission 5 |
  | Legendary | unique effect + 2 | +35% | Mission 8 |
  | Mythic | unique effect + 3 | +50% | Mission 13 |

  Odds of the better rarities rise with each mission and with the Rare Weapon Sensor upgrade.
  Weapons from old saves keep the rarity their perk count gave them.
- **New perks** next to pierce, fire rate, knockback, freeze and bullet speed: **Burn** (damage over 3 s),
  **Chain** (lightning jumps to nearby enemies), **Crit** (chance of double damage), **+1 Shot**,
  **Homing**, **Kill +% Shield** (kills recharge your shield) and **Volatile** (kills explode, hurting
  enemies nearby).
- **10 Legendary/Mythic uniques**, each with a fixed effect: Peacemaker, Leech and Hornet (blasters),
  Dragon Breath and Thunderclap (shotguns), Widowmaker (grenade), Sunlance (laser), Stormcaller (pulse
  gun), Bouncer (pulse shotgun) and Mincer (shredder).

The game's art is fixed at 800×600, so fullscreen scales it up: text and menus stay sharp, sprites are
scaled, and black bars fill the sides of widescreen monitors.

## Build from this repository
This repository holds only the mod (as patches) and its tools, not the game. To build:
1. Put your original game at `original/robokill.swf` (the Miniclip build, sha1 `0893aa0acc151225504640838839832a480b612a`).
2. Have Java 11+ and Python 3 installed (or copy your old `tools/jre` into `tools/`).
3. Run `./build.sh`. The first run downloads JPEXS into `tools/`, decompiles the game into `decompiled/`
   and creates `mod_src/` from `patches/`. Output: `robokill_mod.swf`.

For `./play.sh` and the smoke test, copy your Linux Ruffle into `tools/ruffle/`. For the Windows exe, copy
your `winbuild/ruffle` (patched Ruffle checkout) and `winbuild/toolchain` into `winbuild/`. Or drag
`robokill_mod.swf` onto an existing `RobokillMod.exe` to play it without rebuilding the exe.

## Tweak and rebuild
    ./build.sh                  # regenerates missions + recompiles robokill_mod.swf
    modtools/build_debug.sh     # build/robokill_debug.swf
    winbuild/build_windows.sh   # windows/RobokillMod.exe (after ./build.sh)

| What | Where |
|---|---|
| Frame rate, interpolation, sprite smoothing | `mod_src/GameScene/GameSceneStack.as` (`TARGET_FPS`, `interpolate`, `smoothMovingSprites`) |
| Tier colours / health / XP | `mod_src/ObjectBase/EnemyBase.as` (`toughnessHealthMult`, `toughnessMult`, `extraTierTints`) |
| Tier odds per mission | `mod_src/Scenes/MainScene.as` → `extraTierWeights()` |
| Map size, enemy pools, room difficulty, random seed | `modtools/gen_missions.py` → `MISSIONS` |
| Briefing text | `mod_src/Objects/CommWindow.as` → `extraBriefings` |
| Rarity colours, damage bonus, perk count, value | `mod_src/Weapons/WeaponBase.as` (`rarityColors`, `rarityDamage`, `rarityPerks`, `rarityValue`) |
| Rarity odds, max rarity per mission, uniques | `mod_src/Weapons/WeaponGenerator.as` (`rarityWeights`, `maxRarity()`, `uniques`) |
| Perk strength rolls | `mod_src/WeaponPlugin/WeaponPluginSplash.as` → `roll()` |

The `mod_src/` classes are compiled into `original/robokill.swf` with JPEXS (`tools/ffdec-26.3.0`).
`decompiled/` holds the untouched decompiled source for reference. Edits in `mod_src/` are saved to
`patches/` on every build; commit `patches/`.
For further modding (including by an AI agent), start with `CLAUDE.md`, then `docs/MODDING.md`.
