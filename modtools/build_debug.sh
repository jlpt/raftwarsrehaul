#!/bin/bash
# Debug build: same as robokill_mod.swf (which already has every mission unlocked) but with random
# tiers 0-6 in the extra missions and the weapon test keys (G: drop next rarity, H: drop next unique,
# J: equip 4 uniques; weapons are traced to Ruffle's log). Run ./build.sh first.
set -e
cd "$(dirname "$0")/.."
rm -rf build/debug_src && cp -r mod_src build/debug_src
# random tiers 0-6 in the extra missions so every colour can be eyeballed in one room
sed -i 's/               tier = 3 + i;/               tier = int(Math.random() * 7);/' build/debug_src/Scenes/MainScene.as
grep -q 'int(Math.random() \* 7)' build/debug_src/Scenes/MainScene.as
sed -i 's/public static var debugKeys:Boolean = false;/public static var debugKeys:Boolean = true;/' build/debug_src/Weapons/WeaponGenerator.as
grep -q 'debugKeys:Boolean = true' build/debug_src/Weapons/WeaponGenerator.as
modtools/compile.sh build/debug_src build/robokill_debug.swf
