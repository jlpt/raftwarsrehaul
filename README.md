# Raft Wars: Rehauled

An overhaul mod of the 2007 Flash game **Raft Wars** (Martijn Kunst / BubbleBox).
This repository has **no original game files**. It holds patches, new
ActionScript 2 code, and a build script. The script downloads the original SWF
from the Internet Archive and turns it into `dist/raftwars_rehauled.swf`.

## What's new

**Modes and menus**
- Difficulty select (Easy, Normal, Hard). It changes enemy aim, wind strength, damage, starting credits and a score multiplier.
- **Endless mode**: random battles in waves, with 3 lives. Every wave makes the enemies tougher, more accurate and windier.
- **Continue**: the game auto-saves after every battle and shop purchase.
- **Local high scores** with name entry. These replace the original BubbleBox score server, which no longer exists.
- A "What's New" panel on the title screen.

**Combat**
- **Wind** changes every turn. A gauge at the top shows its direction and strength, and it pushes every shot.
- **Smarter enemies.** The AI simulates its own shot against your crew, and its aim gets better with every shot. On Hard it goes for your weakest crew member. Compared with the original's fixed formula, its accuracy scales with level and difficulty.
- New ammo, in slots 4 and 5:
  - **Triple Shot**: three snowballs fired in a spread.
  - **Mega Bomb**: a huge grenade that explodes on impact, with a much larger blast.
- Bonus credits: **Headshot! +150** and **Splash! +100** (knocking an enemy into the sea).
- A slow-motion letterbox finish when you knock out the last enemy.

**Shop ("Rehauled Armory")**
- Triple Shot, Mega Bomb, **Armor** (3 levels, up to 40% less damage) and **Aim Scope** (3 levels of trajectory preview).
- You can now carry up to 5 rockets and 5 grenades (the original limit was 2).

**Look and feel**
- Lighting changes from morning to dusk as the campaign goes on (afternoon, golden hour, sunset, dusk), and it snows on the viking levels.
- Drop shadows on characters, glowing projectiles with trails, and explosion shockwaves.
- Comic-style popups and UI that use the game's own embedded fonts.

**Quality of life**
- Keys: `1`-`5` pick ammo, `F` toggles fast-forward, `M` toggles music.
- The MochiBot tracker and the dead BubbleBox links were removed.

## Playing

`dist/raftwars_rehauled.swf` runs in any of these:
- **Ruffle desktop** (https://ruffle.rs): open the SWF with it.
- **`dist/raftwars_rehauled.html`**: double-click it to open it in a browser. The SWF is embedded in the file. The [Ruffle](https://ruffle.rs) emulator loads from a CDN, so you need to be online the first time.
- A Flash Player projector (version 8 or newer).

Save data and high scores are stored in the Flash "SharedObject" `raftwars_rehauled`. In a browser, Ruffle keeps it in that browser's local storage.

## Building

You need: `bash`, `curl`, `unzip`, `patch`, `diff`, and Java 11 or newer.

```sh
./build.sh            # download, deobfuscate, patch, compile -> dist/
./build.sh compile    # recompile work/mod (after editing src/ or work/mod)
./build.sh patches    # regenerate patches/ from work/mod vs the clean export
./build.sh html       # wrap the SWF into the self-contained HTML player
DEBUG=1 ./build.sh compile   # adds the test hooks from src/debug/
```

The build is reproducible: a clean checkout produces a byte-identical SWF.

How it works:
1. It downloads `raft-wars.swf` from archive.org and checks its SHA-1 (`f158443e…`, the TASVideos "good dump").
2. It downloads [JPEXS FFDec](https://github.com/jindrapetrik/jpexs-decompiler) 26.3.0 and exports all scripts with AS1/2 deobfuscation turned on. The original code is protected with control-flow obfuscation.
3. It applies `patches/*.patch`, which are small hooks into the original functions.
4. It appends `src/*.as` (all the new systems) to the main game script on frame 4, then recompiles only the scripts it touched back into the SWF.

| Path | Contents |
| --- | --- |
| `src/01_core.as` | state, difficulty table, save/continue, keyboard |
| `src/02_ui.as` | text, buttons, modals, popups |
| `src/03_menu.as` | title screen additions, difficulty select, What's New |
| `src/04_battle.as` | wind, AI aiming, projectiles, ammo slots, scope, effects, kill-cam |
| `src/05_shop.as` | the Rehauled Armory |
| `src/06_scores.as` | local high scores |
| `src/debug/` | ExternalInterface hooks for automated tests (debug builds only) |
| `patches/` | diffs against the deobfuscated original scripts |
| `player/` | the HTML player template |
| `test/` | headless play-test harness (Playwright + Ruffle) and its scenarios |

## Testing

```sh
test/setup.sh                                  # fetch the Ruffle web build
DEBUG=1 ./build.sh compile
node test/run.js dist/raftwars_rehauled.swf test/out/soak test/scenarios/soak.json
```

`soak.json` plays the whole campaign from level 1 to the end with automated
shots and logs each screen transition. The other scenarios cover the menus, the
shop, endless mode, game over, the new ammo, and the level palettes.

## Credits

Raft Wars © 2007 Martijn Kunst / BubbleBox. All original art, sound and code
belong to their owners. This is a non-commercial fan mod; get the original from
its owners or the Internet Archive.
