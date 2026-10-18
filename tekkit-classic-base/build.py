"""Build a late-game Tekkit Classic (3.1.2 / MC 1.2.5) base into a world.

usage: python3 build.py <generated-world-dir> <output-world-dir>

The input world must come from the Tekkit Classic server (so terrain, ores
and rubber trees are real Tekkit worldgen).  Block IDs, tile-entity IDs and
NBT layouts below were taken from the Tekkit Classic 3.1.2 configs and mod
code; item IDs come from data/items.tsv, dumped from the running server.
"""
import os
import shutil
import sys

import numpy as np

from mcworld import (Byte, Compound, Float, Int, List, Long, Short, String,
                     TAG_COMPOUND, World, load_gz, save_gz)

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ data
ITEM_BY_NAME = {}
ITEM_INFO = {}
with open(os.path.join(HERE, "data", "items.tsv")) as fh:
    for line in fh:
        p = line.rstrip("\n").split("\t")
        iid, name = int(p[0]), p[2]
        ITEM_INFO[iid] = {"max_damage": int(p[3]), "max_stack": int(p[4]),
                          "max_charge": int(p[5]) if p[5] and p[1].startswith("ic2") else 0}
        ITEM_BY_NAME.setdefault(name, iid)

OPACITY = np.full(4096, 255, dtype=np.int16)
EMISSION = np.zeros(4096, dtype=np.int16)
OPACITY[0] = 0
with open(os.path.join(HERE, "data", "blocks.tsv")) as fh:
    for line in fh:
        p = line.rstrip("\n").split("\t")
        OPACITY[int(p[0])] = int(p[3])
        EMISSION[int(p[0])] = int(p[4])

# ------------------------------------------------------------ block ids
AIR, STONE, GRASS, DIRT, COBBLE, PLANKS = 0, 1, 2, 3, 4, 5
WATER, GRAVEL, LOG, LEAVES, GLASS = 9, 13, 17, 18, 20
WOOL, GOLD_BLOCK, IRON_BLOCK, DOUBLE_SLAB, SLAB = 35, 41, 42, 43, 44
BOOKSHELF, OBSIDIAN, TORCH, CHEST, DIAMOND_BLOCK = 47, 49, 50, 54, 57
WORKBENCH, WHEAT, FARMLAND, FURNACE, SIGN_POST = 58, 59, 60, 61, 63
WOOD_DOOR, LADDER, WALL_SIGN, LEVER = 64, 65, 68, 69
FENCE, GLOWSTONE, PORTAL, BED, STONE_BRICK = 85, 89, 90, 26, 98
STONE_BRICK_STAIRS, FENCE_GATE, JUKEBOX, LAPIS_BLOCK = 109, 107, 84, 22

# RedPower 2
RP_STONE, RP_STORAGE = 142, 145
MARBLE, BASALT, MARBLE_BRICK, BASALT_COBBLE, BASALT_BRICK = 0, 1, 2, 3, 4
RP_APPLIANCE = 137
# IndustrialCraft 2 (+ addons)
IC_MACHINE, IC_GENERATOR, IC_ELECTRIC, IC_CABLE = 250, 246, 227, 228
IC_REACTOR_CHAMBER, IC_REINF_STONE, IC_REINF_GLASS = 233, 231, 230
IC_RUB_SAPLING, IC_RUB_LEAVES, IC_RUB_WOOD, IC_METAL = 241, 242, 243, 224
ADV_MACHINE, COMPACT_SOLAR, CHARGING_BENCH = 188, 183, 187
IRON_CHEST = 181
# Equivalent Exchange 2
EE_STONE, EE_PEDESTAL, EE_CHEST, EE_TORCH, EE_DEVICE = 126, 127, 128, 129, 130
# BuildCraft
BC_QUARRY, BC_FRAME, BC_ENGINE, BC_PIPE = 153, 160, 161, 166
PIPE_COBBLE, PIPE_STONE, PIPE_GOLD = 4307, 4308, 4310      # pipe item ids (pipeId)
# ComputerCraft
CC_COMPUTER, CC_DISKDRIVE = 207, 208

# IC2 cable types (TileEntityCable.cableType)
CABLE_COPPER, CABLE_GOLD_2X, CABLE_GLASS = 0, 4, 9

# sides (IC2 facing / chest facing): 2=-Z north, 3=+Z south, 4=-X west, 5=+X east
NORTH, SOUTH, WEST, EAST = 2, 3, 4, 5


# ------------------------------------------------------------ item stacks
# names the dump can't resolve uniquely (null name, or charged/empty pairs)
ITEM_ALIASES = {"itemCable": 30184, "itemBatRE": 30242}


def item_id(name):
    if isinstance(name, int):
        return name
    if name in ITEM_ALIASES:
        return ITEM_ALIASES[name]
    key = name if name.startswith("item.") else "item." + name
    if key not in ITEM_BY_NAME:
        raise KeyError("unknown item " + name)
    return ITEM_BY_NAME[key]


def stack(name, count=1, damage=0, charged=False):
    iid = item_id(name)
    count = min(count, ITEM_INFO[iid]["max_stack"])
    tag = Compound({"id": Short(iid), "Count": Byte(count), "Damage": Short(damage)})
    info = ITEM_INFO.get(iid)
    if charged and info and info["max_charge"]:
        tag["Damage"] = Short(1 if info["max_damage"] > 2 else 0)
        tag["tag"] = Compound({"charge": Int(info["max_charge"])})
    return tag


def items(stacks, start=0):
    out = []
    for i, s in enumerate(stacks):
        if s is None:
            continue
        s = Compound(dict(s.value))
        s["Slot"] = Byte(start + i)
        out.append(s)
    return List(TAG_COMPOUND, out)


def many(name, total, damage=0, size=64):
    """Split a big amount into full stacks."""
    out = []
    size = min(size, ITEM_INFO[item_id(name)]["max_stack"])
    while total > 0:
        n = min(size, total)
        out.append(stack(name, n, damage))
        total -= n
    return out


# ================================================================ builder
class Builder:
    def __init__(self, world):
        self.w = world

    def set(self, x, y, z, b, m=0):
        if self.w.get(x, y, z) not in (None, (0, 0)):
            self.w.remove_tile(x, y, z)
        self.w.set(x, y, z, b, m)

    def fill(self, x0, y0, z0, x1, y1, z1, b, m=0):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, b, m)

    def tile(self, x, y, z, b, m, te_id, **fields):
        self.set(x, y, z, b, m)
        self.w.add_tile(x, y, z, te_id, fields)

    # -- vanilla helpers
    def chest(self, x, y, z, facing, stacks):
        self.tile(x, y, z, CHEST, facing, "Chest", Items=items(stacks))

    def furnace(self, x, y, z, facing, stacks=()):
        self.tile(x, y, z, FURNACE, facing, "Furnace", Items=items(stacks),
                  BurnTime=Short(0), CookTime=Short(0))

    def sign(self, x, y, z, facing, lines, wall=True):
        lines = (list(lines) + ["", "", "", ""])[:4]
        fields = {"Text%d" % (i + 1): String(t[:15]) for i, t in enumerate(lines)}
        if wall:
            self.tile(x, y, z, WALL_SIGN, facing, "Sign", **fields)
        else:
            rotation = {SOUTH: 0, WEST: 4, NORTH: 8, EAST: 12}[facing]
            self.tile(x, y, z, SIGN_POST, rotation, "Sign", **fields)

    def door(self, x, y, z, direction, right_hinge=False):
        self.set(x, y, z, WOOD_DOOR, direction)
        self.set(x, y + 1, z, WOOD_DOOR, 8 | (1 if right_hinge else 0))

    # -- modded helpers
    def ic2(self, x, y, z, b, m, te_id, facing, **extra):
        self.tile(x, y, z, b, m, te_id, facing=Short(facing), **extra)

    def cable(self, x, y, z, ctype):
        self.tile(x, y, z, IC_CABLE, 0, "Cable", cableType=Short(ctype), color=Short(0),
                  foamed=Byte(0), foamColor=Byte(0), facing=Short(0))

    def pipe(self, x, y, z, pipe_id):
        self.tile(x, y, z, BC_PIPE, 0, "net.minecraft.src.buildcraft.transport.GenericPipe",
                  pipeId=Int(pipe_id))

    def iron_chest(self, x, y, z, kind, facing, stacks=()):
        names = {0: "IRON", 1: "GOLD", 2: "DIAMOND", 3: "COPPER", 4: "SILVER", 5: "CRYSTAL"}
        self.tile(x, y, z, IRON_CHEST, kind, names[kind], facing=Byte(facing), Items=items(stacks))

    def ee(self, x, y, z, b, m, te_id, direction=NORTH, **extra):
        self.tile(x, y, z, b, m, te_id, direction=Byte(direction), player=String(""), **extra)


# =================================================================== site
def ground_height(w, x, z):
    skip = {0, 17, 18, 31, 32, 37, 38, 39, 40, 78, 83, 81, 86, 106,
            IC_RUB_SAPLING, IC_RUB_LEAVES, IC_RUB_WOOD, 139, 141, 143, 144}
    for y in range(110, 0, -1):
        b, _ = w.get(x, y, z)
        if b not in skip:
            return y
    return 0


def prepare_site(b, x0, z0, x1, z1, G, margin=6):
    """Flatten [x0..x1]x[z0..z1] to grass at y=G and clear everything above.

    A sloped margin blends the pad into the surrounding terrain.
    """
    w = b.w
    for x in range(x0 - margin, x1 + margin + 1):
        for z in range(z0 - margin, z1 + margin + 1):
            dx = max(x0 - x, 0, x - x1)
            dz = max(z0 - z, 0, z - z1)
            d = max(dx, dz)
            nat = ground_height(w, x, z)
            if d == 0:
                target = G
            else:
                t = d / (margin + 1)
                target = round(G * (1 - t) + nat * t)
            for y in range(target + 1, 110):
                if w.get(x, y, z)[0] != 0:
                    b.set(x, y, z, AIR)
            for y in range(target - 3, target):
                if w.get(x, y, z)[0] in (0, 8, 9, 12, 13, 31, 78, 79):
                    b.set(x, y, z, DIRT)
            b.set(x, target, z, GRASS)


# ================================================================ the base
def build_base(w, BX, BZ, G):
    b = Builder(w)
    W, D = 31, 23                      # hall footprint (x 0..30, z 0..22)
    F2, RF = 6, 12                     # floor-2 slab / roof slab (relative y)

    def A(rx, ry, rz):                 # hall-relative -> absolute
        return BX + rx, G + ry, BZ + rz

    def hset(rx, ry, rz, blk, m=0):
        b.set(*A(rx, ry, rz), blk, m)

    def hfill(rx0, ry0, rz0, rx1, ry1, rz1, blk, m=0):
        x0, y0, z0 = A(rx0, ry0, rz0)
        x1, y1, z1 = A(rx1, ry1, rz1)
        b.fill(x0, y0, z0, x1, y1, z1, blk, m)

    # ---------------------------------------------------------- shell
    hfill(0, 0, 0, W - 1, 0, D - 1, DOUBLE_SLAB)                # floor 1
    hfill(0, -3, 0, W - 1, -1, D - 1, STONE)                    # foundation
    hfill(0, F2, 0, W - 1, F2, D - 1, RP_STONE, MARBLE_BRICK)   # floor 2
    hfill(0, RF, 0, W - 1, RF, D - 1, IC_REINF_STONE)           # roof
    pillars_x = (0, 6, 12, 18, 24, 30)
    pillars_z = (0, 11, 22)
    for ry in range(0, RF + 1):
        for rx in range(W):
            for rz in (0, D - 1):
                hset(rx, ry, rz, RP_STONE, BASALT_BRICK)
        for rz in range(D):
            for rx in (0, W - 1):
                hset(rx, ry, rz, RP_STONE, BASALT_BRICK)
    # windows (reinforced glass) between pillars on both floors
    for ry in list(range(2, 5)) + list(range(F2 + 2, F2 + 5)):
        for rx in range(W):
            if min(abs(rx - p) for p in pillars_x) >= 2:
                hset(rx, ry, 0, IC_REINF_GLASS)
                hset(rx, ry, D - 1, IC_REINF_GLASS)
        for rz in range(D):
            if min(abs(rz - p) for p in pillars_z) >= 2:
                hset(0, ry, rz, IC_REINF_GLASS)
                hset(W - 1, ry, rz, IC_REINF_GLASS)
    # marble trim: pillars and horizontal bands
    for ry in range(0, RF + 2):
        for rx in pillars_x:
            for rz in (0, D - 1):
                hset(rx, ry, rz, RP_STONE, MARBLE_BRICK)
        for rz in pillars_z:
            for rx in (0, W - 1):
                hset(rx, ry, rz, RP_STONE, MARBLE_BRICK)
    for ry in (0, F2, RF):
        for rx in range(W):
            hset(rx, ry, 0, RP_STONE, MARBLE_BRICK)
            hset(rx, ry, D - 1, RP_STONE, MARBLE_BRICK)
        for rz in range(D):
            hset(0, ry, rz, RP_STONE, MARBLE_BRICK)
            hset(W - 1, ry, rz, RP_STONE, MARBLE_BRICK)
    # roof parapet with glowstone caps on the pillars
    for rx in range(W):
        for rz in (0, D - 1):
            hset(rx, RF + 1, rz, RP_STONE, BASALT_BRICK)
    for rz in range(D):
        for rx in (0, W - 1):
            hset(rx, RF + 1, rz, RP_STONE, BASALT_BRICK)
    for rx in pillars_x:
        for rz in (0, D - 1):
            hset(rx, RF + 2, rz, GLOWSTONE)
    for rz in pillars_z:
        for rx in (0, W - 1):
            hset(rx, RF + 2, rz, GLOWSTONE)
    # ceiling lights
    for rx in range(3, W - 1, 4):
        for rz in range(3, D - 1, 4):
            hset(rx, F2, rz, GLOWSTONE)
            hset(rx, RF, rz, GLOWSTONE)

    # entrance (south, 3 wide archway) + porch roof, north service door
    hfill(14, 1, D - 1, 16, 3, D - 1, AIR)
    hfill(13, 4, D, 17, 4, D + 1, SLAB, 0)
    for rx in (13, 17):
        hfill(rx, 1, D + 1, rx, 3, D + 1, RP_STONE, MARBLE_BRICK)
    b.door(*A(15, 1, 0), 3)

    # ------------------------------------------------- floor 1: power
    # HV backbone: roof solar cables -> duct in NE corner -> under-floor -> MFSUs
    for rx in range(19, 30):
        b.cable(*A(rx, RF, 3), CABLE_GLASS)
        b.cable(*A(rx, RF, 5), CABLE_GLASS)
    b.cable(*A(29, RF, 4), CABLE_GLASS)
    for ry in range(0, RF):
        b.cable(*A(29, ry, 3), CABLE_GLASS)
    for rz in range(4, 12):
        b.cable(*A(29, 0, rz), CABLE_GLASS)
    for ry in list(range(1, F2)) + list(range(F2 + 1, RF)):      # glass duct
        hset(28, ry, 3, IC_REINF_GLASS)
        hset(29, ry, 2, IC_REINF_GLASS)
        hset(29, ry, 4, IC_REINF_GLASS)
    # High-voltage solar arrays on the roof (512 EU/t each in daylight)
    for rx in range(19, 30, 2):
        for rz in (3, 5):
            b.tile(*A(rx, RF + 1, rz), COMPACT_SOLAR, 2, "CompactSolarType.HV", Items=items([]))
    # MFSU bank, outputs facing west
    mfsu_charge = [8000000, 9500000, 6000000, 10000000]
    for i, rz in enumerate((5, 7, 9, 11)):
        b.ic2(*A(29, 1, rz), IC_ELECTRIC, 2, "MFSU", WEST, energy=Int(mfsu_charge[i]),
              redstoneMode=Byte(0), Items=items([]))
    # MFSU A -> MV transformer -> LV transformer -> under-floor glass-fibre bus
    # (glass fibre: 0.025 EU/block loss; copper starves far machines in IC2 1.97)
    b.ic2(*A(28, 1, 5), IC_ELECTRIC, 4, "MV-Transformer", EAST, energy=Int(0))
    b.ic2(*A(27, 1, 5), IC_ELECTRIC, 3, "LV-Transformer", EAST, energy=Int(0))
    for rx in range(3, 28):
        b.cable(*A(rx, 0, 5), CABLE_GLASS)
    # MV (128 EU/t) consumer: induction furnace on the MV transformer's north face
    b.ic2(*A(28, 1, 4), IC_MACHINE, 13, "Induction Furnace", WEST, energy=Int(0),
          Items=items([stack("itemDustIron", 32), stack("itemDustCopper", 32)]))
    # MFSU B -> mass fabricator (accepts 512), MFSU C -> charging bench Mk3
    b.ic2(*A(28, 1, 7), IC_MACHINE, 14, "Mass Fabricator", WEST, energy=Int(0),
          Items=items([stack("itemScrap", 64)]))
    b.ic2(*A(28, 1, 9), CHARGING_BENCH, 2, "Charging Bench Mk3", WEST, energy=Int(0),
          Items=items([stack("itemBatCrystal", 1), stack("itemBatLamaCrystal", 1),
                       stack("itemBatRE", 1)]))
    b.sign(*A(26, 3, 1), SOUTH, ["POWER ROOM", "12x HV Solar", "4x MFSU", "MV/LV transf."])

    # LV machine bank on top of the copper bus (fronts face south)
    bank = [
        (24, IC_MACHINE, 3, "Macerator", [stack(15, 48)]),                       # iron ore
        (22, IC_MACHINE, 3, "Macerator", [stack(IC_METAL_ORE_COPPER, 40)]),
        (20, IC_MACHINE, 2, "Electric Furnace", [stack("itemDustIron", 48)]),
        (18, IC_MACHINE, 2, "Electric Furnace", [stack("itemDustCopper", 32)]),
        (16, ADV_MACHINE, 0, "Rotary Macerator", [stack(14, 24)]),               # gold ore
        (14, ADV_MACHINE, 1, "Singularity Compressor", [stack(12, 64)]),         # sand
        (12, ADV_MACHINE, 2, "Centrifuge Extractor", [stack("itemHarz", 24)]),
        (10, IC_MACHINE, 4, "Extractor", []),
        (8, IC_MACHINE, 5, "Compressor", [stack(12, 64)]),                        # sand
        (6, IC_MACHINE, 11, "Recycler", [stack(4, 64)]),                         # cobble
        (4, IC_MACHINE, 6, "Canning Machine", []),
    ]
    for rx, blk, meta, te, stacks in bank:
        b.ic2(*A(rx, 1, 5), blk, meta, te, SOUTH, energy=Int(0), Items=items(stacks))
    for rx in range(5, 26, 2):
        hset(rx, 1, 5, IC_MACHINE, 0)                                 # machine casings
    hset(3, 1, 5, IC_MACHINE, 12)                                     # advanced casing
    # second row (z=12), fed by a copper branch off the bus at x=16
    for rz in range(6, 13):
        b.cable(*A(16, 0, rz), CABLE_GLASS)
    for rx in range(6, 25):
        b.cable(*A(rx, 0, 12), CABLE_GLASS)
    row2 = [
        (23, IC_MACHINE, 2, "Electric Furnace", [stack("itemDustGold", 16)]),
        (21, IC_MACHINE, 2, "Electric Furnace", [stack("itemDustTin", 24)]),
        (19, IC_MACHINE, 3, "Macerator", [stack(248, 32)]),                     # tin ore
        (17, IC_MACHINE, 3, "Macerator", [stack(4, 64)]),                       # cobble -> sand
        (15, IC_MACHINE, 5, "Compressor", [stack("itemPartCoalBall", 4)]),
        (13, IC_MACHINE, 4, "Extractor", [stack(IC_RUB_WOOD, 16)]),
        (11, IC_MACHINE, 2, "Electric Furnace", [stack(12, 64)]),               # sand -> glass
        (9, IC_MACHINE, 3, "Macerator", [stack(13, 32)]),
        (7, IC_MACHINE, 11, "Recycler", [stack(3, 64)]),
    ]
    for rx, blk, meta, te, stacks in row2:
        b.ic2(*A(rx, 1, 12), blk, meta, te, NORTH, energy=Int(0), Items=items(stacks))
    for rx in range(8, 24, 2):
        hset(rx, 1, 12, IC_MACHINE, 0)
    b.iron_chest(*A(6, 1, 12), 2, NORTH, many("itemDustIron", 128) + many(265, 192))
    b.iron_chest(*A(24, 1, 12), 2, NORTH, many(20, 256) + many(12, 128))

    # labels on the wall behind the bank
    labels = {24: "Macerator", 20: "E-Furnace", 16: "Rotary Mac.", 12: "Centrifuge",
              8: "Compressor", 4: "Canner"}
    for rx, txt in labels.items():
        b.sign(*A(rx, 3, 1), SOUTH, ["", txt, "", ""])

    # ----------------------------------------- floor 1: workshop / lobby
    hset(1, 1, 8, WORKBENCH)
    b.tile(*A(1, 1, 9), RP_APPLIANCE, 3, "RPAdvBench", rot=Byte(1), ps=Byte(0), Items=items([]))
    b.tile(*A(1, 1, 10), RP_APPLIANCE, 0, "RPAFurnace", rot=Byte(1), ps=Byte(0), Items=items([]))
    b.furnace(*A(1, 1, 11), EAST, [None, stack(263, 32)])
    b.furnace(*A(1, 1, 12), EAST, [None, stack(263, 32)])
    b.ic2(*A(1, 1, 13), IC_MACHINE, 1, "Iron Furnace", EAST, Items=items([]))
    hset(1, 1, 14, WORKBENCH)
    for rz, txt in ((9, "Project Table"), (10, "Alloy Furnace"), (13, "Iron Furnace")):
        b.sign(*A(1, 3, rz), EAST, ["", txt, "", ""])
    # central work tables
    for rx in (8, 9, 10):
        hset(rx, 1, 16, WORKBENCH)
    b.chest(*A(11, 1, 16), NORTH, [stack(280, 64), stack(5, 64), stack(4, 64),
                                    stack(331, 64), stack(265, 32), stack(20, 64)])
    b.chest(*A(7, 1, 16), NORTH, [stack("itemPartCircuit", 32), stack("itemCable", 64, 0),
                                   stack("itemCable", 32, 9), stack("itemRubber", 64),
                                   stack("itemIngotAdvIron", 48), stack(IC_MACHINE, 16, 0)])

    # stairs to floor 2 (west wall, climbing north)
    for k in range(6):
        for rx in (1, 2):
            hset(rx, 1 + k, 21 - k, STONE_BRICK_STAIRS, 3)
            for ry in range(1, 1 + k):
                hset(rx, ry, 21 - k, RP_STONE, BASALT_BRICK)
    for rz in (17, 18):
        hset(1, F2, rz, AIR)
        hset(2, F2, rz, AIR)

    # lobby
    b.sign(*A(13, 3, D - 2), NORTH, ["Tekkit Classic", "TECH BASE", "Welcome home!", ""])
    b.chest(*A(12, 1, D - 2), NORTH, starter_kit())
    b.sign(*A(17, 3, D - 2), NORTH, ["Upstairs:", "Storage, EE Lab", "Quarters, Roof", ""])
    b.sign(*A(18, 2, D - 2), NORTH, ["Outside:", "N: Quarry", "E: Reactor", "W: Farm+Portal"])

    # ----------------------------------------- floor 2: interior walls
    Y2 = F2 + 1
    hfill(14, Y2, 1, 14, RF - 1, D - 2, RP_STONE, MARBLE_BRICK)
    hfill(15, Y2, 11, W - 2, RF - 1, 11, RP_STONE, MARBLE_BRICK)
    for rz in (6, 15):
        hfill(14, Y2, rz, 14, Y2 + 1, rz, AIR)
    hfill(22, Y2, 11, 22, Y2 + 1, 11, AIR)
    # stair railing
    for rz in range(16, 20):
        hset(3, Y2, rz, FENCE)
    hset(1, Y2, 19, FENCE)
    hset(2, Y2, 19, FENCE)

    # ------------------------------------------- floor 2: storage vault
    vault = iter(vault_contents())
    slots = [(1, rz, EAST) for rz in range(2, 15)] + [(rx, 1, SOUTH) for rx in range(2, 13)]
    for (rx, rz, face) in slots:
        labels = []
        for ry in (Y2, Y2 + 1):
            label, stacks = next(vault, ("", []))
            labels.append(label)
            b.iron_chest(*A(rx, ry, rz), 2, face, stacks)
        if any(labels):
            b.sign(*A(rx, Y2 + 2, rz), face, ["Top:", labels[1] or "(empty)",
                                               "Bottom:", labels[0] or "(empty)"])
    # gold-block / diamond-block display plinths
    for rx, blk in ((6, DIAMOND_BLOCK), (8, GOLD_BLOCK), (10, LAPIS_BLOCK)):
        hset(rx, Y2, 8, blk)
    hset(8, Y2, 10, RP_STORAGE, 0)
    hset(6, Y2, 10, RP_STORAGE, 1)
    hset(10, Y2, 10, RP_STORAGE, 2)

    # ------------------------------------------------ floor 2: EE lab
    b.ee(*A(22, Y2, 5), EE_DEVICE, 0, "Transmutation Tablet", Items=items([]))
    b.sign(*A(22, Y2 + 2, 1), SOUTH, ["", "EE LAB", "", ""])
    b.ee(*A(16, Y2, 1), EE_CHEST, 0, "Alchemical Chest", SOUTH, Items=items(ee_chest_1()))
    b.ee(*A(17, Y2, 1), EE_CHEST, 0, "Alchemical Chest", SOUTH, Items=items(ee_chest_2()))
    b.ee(*A(19, Y2, 1), EE_STONE, 3, "Dark Matter Furnace", SOUTH,
         Items=items([stack("alchemicalCoal", 32)]))
    b.ee(*A(20, Y2, 1), EE_STONE, 4, "Red Matter Furnace", SOUTH,
         Items=items([stack("mobiusFuel", 16)]))
    b.ee(*A(25, Y2, 8), EE_PEDESTAL, 0, "Pedestal", Items=items([]))
    b.ee(*A(16, Y2, 9), EE_STONE, 8, "DM Block")
    b.ee(*A(16, Y2 + 1, 9), EE_STONE, 9, "RM Block")
    b.ee(*A(27, Y2, 9), EE_STONE, 8, "DM Block")
    b.ee(*A(27, Y2 + 1, 9), EE_STONE, 9, "RM Block")
    hset(16, Y2 + 2, 9, EE_TORCH, 5)
    hset(27, Y2 + 2, 9, EE_TORCH, 5)
    b.sign(*A(24, Y2 + 2, 1), SOUTH, ["Condenser +", "collectors", "are on the", "roof!"])

    # ---------------------------------------------- floor 2: quarters
    bx_, by_, bz_ = A(17, Y2, 20)
    b.set(bx_, by_, bz_, BED, 2)                 # foot (pointing north)
    b.set(bx_, by_, bz_ - 1, BED, 2 | 8)         # head
    b.chest(*A(16, Y2, 21), NORTH, food_chest())
    hfill(19, Y2, 21, 22, Y2 + 1, 21, BOOKSHELF)
    hset(23, Y2, 21, JUKEBOX)
    for rz, (lbl, stacks) in zip(range(13, 18), armory()):
        b.iron_chest(*A(29, Y2, rz), 2, WEST, stacks)
        b.sign(*A(29, Y2 + 1, rz), WEST, ["", lbl, "", ""])
    b.tile(*A(20, Y2, 13), CC_COMPUTER, SOUTH, "computer", on=Byte(1), userDir=String("0"))
    b.tile(*A(21, Y2, 13), CC_DISKDRIVE, SOUTH, "diskdrive", Items=items([]))
    b.sign(*A(20, Y2 + 2, 12), SOUTH, ["Base Computer", "right-click it", "for the base", "guide"])
    # ladder to the roof (east wall)
    for ry in range(Y2, RF + 1):
        hset(29, ry, 21, LADDER, 4)

    # ------------------------------------------------------ roof: EMC
    YR = RF + 1
    cx, cz = 7, 11
    b.ee(*A(cx, YR, cz), EE_CHEST, 1, "Energy Condenser", SOUTH,
         Items=items([stack(264, 1)]), scaledEnergy=Int(0), eternalDensity=Short(0))
    b.chest(*A(cx, YR + 1, cz), SOUTH, [])
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        b.ee(*A(cx + dx, YR, cz + dz), EE_STONE, 7, "Antimatter Array MK3", SOUTH, Items=items([]))
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
        b.ee(*A(cx + dx, YR, cz + dz), EE_STONE, 2, "Energy Collector MK3", SOUTH, Items=items([]))
    b.sign(*A(cx, YR, cz + 4), SOUTH, ["EMC FARM", "8x Collector MK3", "4x Relay MK3", "-> Diamonds"],
           wall=False)
    # deck lighting
    for rx, rz in ((3, 3), (3, 19), (12, 3), (12, 19), (16, 11), (24, 15), (24, 19)):
        hset(rx, RF, rz, GLOWSTONE)
    b.sign(*A(24, YR, 8), SOUTH, ["SOLAR FIELD", "12x HV Solar", "Array (512EU/t)", ""], wall=False)
    return b


IC_METAL_ORE_COPPER = 249


# ============================================================ outbuildings
def build_reactor(b, x0, z0, G):
    """Reinforced reactor bunker with an EMPTY nuclear reactor."""
    x1, z1 = x0 + 8, z0 + 10
    b.fill(x0, G, z0, x1, G, z1, IC_REINF_STONE)
    for y in range(G + 1, G + 6):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                b.set(x, y, z, IC_REINF_STONE if edge else AIR)
    b.fill(x0, G + 6, z0, x1, G + 6, z1, IC_REINF_STONE)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                b.set(x, G + 5, z, WOOL, 4 if (x + z) % 2 else 15)      # yellow/black
    for z in range(z0 + 2, z1 - 1):
        for y in (G + 2, G + 3):
            if z != z0 + 5:
                b.set(x1, y, z, IC_REINF_GLASS)
    for x, z in ((x0 + 2, z0 + 2), (x1 - 2, z0 + 2), (x0 + 2, z1 - 2), (x1 - 2, z1 - 2)):
        b.set(x, G + 6, z, GLOWSTONE)
    b.door(x0, G + 1, z0 + 5, 0)
    rx, ry, rz = x0 + 4, G + 2, z0 + 5
    b.set(rx, ry - 1, rz, IC_REINF_STONE)
    b.ic2(rx, ry, rz, IC_GENERATOR, 5, "Nuclear Reactor", WEST, Items=items([]), heat=Int(0))
    for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0)):
        b.ic2(rx + dx, ry + dy, rz + dz, IC_REACTOR_CHAMBER, 0, "Reactor Chamber", WEST)
    b.iron_chest(x0 + 1, G + 1, z0 + 1, 2, SOUTH, [
        stack("itemCellUran", 8), stack("itemCellCoolant", 32),
        stack("itemReactorPlating", 16), stack("itemReactorCooler", 16),
        stack(79, 64), stack("itemCellEmpty", 32)])
    b.sign(x0 + 1, G + 3, z0 + 1, SOUTH, ["REACTOR PARTS", "", "", ""])
    b.sign(x0 + 1, G + 2, z0 + 4, EAST, ["!! REACTOR !!", "It is EMPTY.", "Design cooling", "before fuel!"])


def build_quarry(b, qx, qz, G):
    """BuildCraft quarry (11x11) with 3 redstone engines, lever-controlled."""
    y = G + 1
    xmin, xmax, zmin, zmax = qx - 5, qx + 5, qz - 11, qz - 1
    # quarry: meta 3 (box lies north / ZNeg)
    b.tile(qx, y, qz, BC_QUARRY, 3, "Machine", xMin=Int(xmin), zMin=Int(zmin),
           xSize=Int(11), ySize=Int(5), zSize=Int(11),
           targetX=Int(xmin + 1), targetY=Int(y), targetZ=Int(zmin + 1), world=String("world"))
    # pre-built frame exactly where the quarry's blueprint wants it
    for yy in (y, y + 4):
        for x in range(xmin, xmax + 1):
            b.set(x, yy, zmin, BC_FRAME)
            b.set(x, yy, zmax, BC_FRAME)
        for z in range(zmin, zmax + 1):
            b.set(xmin, yy, z, BC_FRAME)
            b.set(xmax, yy, z, BC_FRAME)
    for yy in range(y + 1, y + 4):
        for x, z in ((xmin, zmin), (xmin, zmax), (xmax, zmin), (xmax, zmax)):
            b.set(x, yy, z, BC_FRAME)
    # engines (BuildCraft Orientations: 2=ZNeg 4=XNeg 5=XPos)
    for ex, ez, orient in ((qx - 1, qz, 5), (qx + 1, qz, 4), (qx, qz + 1, 2)):
        b.tile(ex, y, ez, BC_ENGINE, 0, "net.minecraft.src.buildcraft.energy.Engine",
               kind=Int(0), orientation=Int(orient), progress=Float(0), energy=Int(0))
    for px in (qx - 1, qx + 1):
        b.set(px, y, qz + 1, IRON_BLOCK)
        b.set(px, y + 1, qz + 1, LEVER, 5)
    # output: pipe from the top of the quarry into the hall's quarry chest
    route = [(qx, y + 1, qz), (qx + 1, y + 1, qz), (qx + 2, y + 1, qz)]
    route += [(qx + 2, y + 1, z) for z in range(qz + 1, qz + 9)]
    for i, (px, py, pz) in enumerate(route):
        b.pipe(px, py, pz, PIPE_GOLD if i % 4 == 3 else PIPE_STONE)
    b.iron_chest(qx + 2, y, qz + 8, 2, NORTH, [])
    b.sign(qx, y, qz + 2, SOUTH, ["QUARRY", "Flip BOTH", "levers to run", "-> pipe to hall"], wall=False)


def build_farm(b, x0, z0, G):
    """Two 9x9 wheat fields with a fence and lamp posts."""
    for fx in (x0, x0 + 11):
        cx, cz = fx + 5, z0 + 5
        for x in range(fx, fx + 11):
            for z in range(z0, z0 + 11):
                edge = x in (fx, fx + 10) or z in (z0, z0 + 10)
                if edge:
                    b.set(x, G, z, GRASS)
                    b.set(x, G + 1, z, FENCE)
                elif (x, z) == (cx, cz):
                    b.set(x, G, z, WATER)
                    b.set(x, G + 1, z, AIR)
                else:
                    b.set(x, G, z, FARMLAND, 7)
                    b.set(x, G + 1, z, WHEAT, 7)
        b.set(cx, G + 1, z0, FENCE_GATE, 0)
        for x, z in ((fx, z0), (fx + 10, z0), (fx, z0 + 10), (fx + 10, z0 + 10)):
            b.set(x, G + 2, z, FENCE)
            b.set(x, G + 3, z, GLOWSTONE)
    b.sign(x0 + 5, G + 1, z0 - 2, NORTH, ["WHEAT FARM", "", "", ""], wall=False)


def rubber_tree(b, x, z, G, h=6):
    for y in range(G + 1, G + 1 + h):
        b.set(x, y, z, IC_RUB_WOOD, 0)
    for side, y in ((2, G + 2), (3, G + 3), (4, G + 4), (5, G + 2)):
        b.set(x, y, z, IC_RUB_WOOD, side)          # wet resin spots
    top = G + h
    for dy in range(-2, 3):
        r = 2 if dy < 1 else 1
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx == dz == 0 and dy <= 0:
                    continue
                if abs(dx) == abs(dz) == 2:
                    continue
                if b.w.get(x + dx, top + dy, z + dz)[0] == AIR:
                    b.set(x + dx, top + dy, z + dz, IC_RUB_LEAVES, 0)
    b.set(x, top + 1, z, IC_RUB_LEAVES, 0)


def build_portal(b, x0, z, G):
    """Lit nether portal (inner 2x3) along the X axis."""
    for x in range(x0, x0 + 4):
        b.set(x, G + 1, z, OBSIDIAN)
        b.set(x, G + 5, z, OBSIDIAN)
    for y in range(G + 2, G + 5):
        b.set(x0, y, z, OBSIDIAN)
        b.set(x0 + 3, y, z, OBSIDIAN)
        b.set(x0 + 1, y, z, PORTAL)
        b.set(x0 + 2, y, z, PORTAL)
    b.sign(x0 + 1, G + 1, z + 2, SOUTH, ["NETHER", "PORTAL", "(Nether Ores", "inside!)"], wall=False)


def lamp_post(b, x, z, G):
    b.set(x, G + 1, z, FENCE)
    b.set(x, G + 2, z, FENCE)
    b.set(x, G + 3, z, GLOWSTONE)


# =========================================================== chest loot
def starter_kit():
    return [
        stack(278, 1), stack(276, 1), stack(277, 1), stack(279, 1),          # diamond tools
        stack("itemToolWrench", 1), stack("itemTreetap", 1), stack("itemToolMeter", 1),
        stack(320, 32), stack(297, 32), stack(364, 32),                       # food
        stack(50, 64), stack(58, 4), stack(54, 4),
        stack("philStone", 1), stack("itemToolDrill", 1, charged=True),
        stack("itemBatRE", 4), stack(4062, 1), stack(1262, 1),                # BC wrench, RP2 screwdriver
        stack(346, 1), stack(345, 1), stack(347, 1),
    ]


def food_chest():
    return [stack(320, 64), stack(364, 64), stack(297, 64), stack(357, 64),
            stack(260, 32), stack(322, 8), stack(350, 32), stack(366, 32),
            stack(282, 1), stack(354, 1)]


def armory():
    return [
        ("Quantum Suit", [stack("itemArmorQuantumHelmet", charged=True),
                          stack("itemArmorQuantumChestplate", charged=True),
                          stack("itemArmorQuantumLegs", charged=True),
                          stack("itemArmorQuantumBoots", charged=True),
                          None,
                          stack("itemArmorNanoHelmet", charged=True),
                          stack("itemArmorNanoChestplate", charged=True),
                          stack("itemArmorNanoLegs", charged=True),
                          stack("itemArmorNanoBoots", charged=True)]),
        ("IC2 Tools", [stack("itemToolMiningLaser", charged=True),
                       stack("itemToolDDrill", charged=True),
                       stack("itemToolChainsaw", charged=True),
                       stack(30148, 1, charged=True),                          # nano saber
                       stack("itemScannerAdv", charged=True),
                       stack("itemToolWrenchElectric", charged=True),
                       stack("itemTreetapElectric", charged=True),
                       stack("itemArmorJetpackElectric", charged=True),
                       stack("itemArmorLappack", charged=True),
                       stack("itemArmorBatpack", charged=True)]),
        ("Matter Tools", [stack("darkPickaxe"), stack("darkSword"), stack("darkAxe"),
                          stack("darkSpade"), stack("darkHammer"), stack("darkShears"),
                          stack("redPickaxe"), stack("redSword"), stack("redAxe"),
                          stack("redSpade"), stack("redHammer"), stack("redKatar"),
                          stack("redMace")]),
        ("Matter Armor", [stack("redMatterHelmet"), stack("redMatterArmor"),
                          stack("redMatterGreaves"), stack("redMatterBoots"), None,
                          stack("darkMatterHelmet"), stack("darkMatterArmor"),
                          stack("darkMatterGreaves"), stack("darkMatterBoots")]),
        ("Rings + Gear", [stack("swiftWolfRing"), stack("harvestRing"), stack("ignitionRing"),
                          stack("zeroRing"), stack("evertide"), stack("volcanite"),
                          stack("attractionRing"), stack("diviningRod"), stack("repairCharm"),
                          stack("alchemyBag", 1, 0), stack("transTablet"),
                          stack(261, 1), stack(262, 64), stack(26514, 1), stack(26517, 64)]),
    ]


def ee_chest_1():
    return [stack("darkMatter", 32), stack("redMatter", 16), stack("alchemicalCoal", 64),
            stack("mobiusFuel", 32), stack("aeternalisFuel", 8), stack("covalenceDust", 64, 0),
            stack("covalenceDust", 64, 1), stack("covalenceDust", 64, 2),
            stack(EE_STONE, 4, 2), stack(EE_STONE, 2, 7), stack(EE_CHEST, 1, 1)]


def ee_chest_2():
    return [stack(264, 64), stack(57, 16), stack(266, 64), stack(41, 16),
            stack(368, 16), stack(369, 16), stack(372, 32), stack(348, 64), stack(89, 32)]


def vault_contents():
    """(label, stacks) for each vault chest, in placement order."""
    return [
        ("Ores", many(15, 256) + many(14, 128) + many(IC_METAL_ORE_COPPER, 192)
         + many(248, 192) + many(247, 32) + many(56, 32) + many(73, 64) + many(21, 64)),
        ("Ingots", many(265, 512) + many(266, 256) + many("itemIngotCopper", 384)
         + many("itemIngotTin", 256) + many("itemIngotBronze", 128)
         + many("itemIngotAdvIron", 192)),
        ("Gems", many(264, 192) + many(331, 512) + many(351, 192, damage=4)
         + many(348, 128) + many(1257, 64, 0) + many(1257, 64, 1) + many(1257, 64, 2)
         + many(1257, 192, 6)),
        ("Dusts", many("itemDustIron", 128) + many("itemDustGold", 64)
         + many("itemDustCopper", 128) + many("itemDustTin", 128)
         + many("itemDustCoal", 128) + many("itemDustBronze", 64)
         + many(1257, 128, 3) + many(1257, 128, 4) + many(1257, 128, 5)),
        ("Circuits", many("itemPartCircuit", 256) + many("itemPartCircuitAdv", 96)
         + many("itemPartAlloy", 128) + many("itemPartCarbonPlate", 96)
         + many("itemPartCarbonFibre", 64) + many("itemPartIridium", 16)
         + many("itemOreIridium", 32) + many("itemMatter", 64)
         + many("itemPartIndustrialDiamond", 32)),
        ("Cables", many("itemCable", 256, 0) + many("itemCable", 128, 4)
         + many("itemCable", 192, 9) + many("itemCable", 128, 8)
         + many("itemRubber", 256) + many("itemHarz", 128)),
        ("Machines", [stack(IC_MACHINE, 32, 0), stack(IC_MACHINE, 16, 12),
                      stack(IC_MACHINE, 4, 3), stack(IC_MACHINE, 4, 2),
                      stack(IC_MACHINE, 2, 4), stack(IC_MACHINE, 2, 5),
                      stack(IC_MACHINE, 2, 11), stack(IC_GENERATOR, 8, 0),
                      stack(IC_GENERATOR, 8, 1), stack(IC_GENERATOR, 16, 3),
                      stack(IC_ELECTRIC, 4, 0), stack(IC_ELECTRIC, 2, 1),
                      stack(IC_ELECTRIC, 2, 2), stack(IC_ELECTRIC, 2, 3),
                      stack(IC_ELECTRIC, 2, 4), stack(IC_ELECTRIC, 1, 5),
                      stack(COMPACT_SOLAR, 4, 0), stack(COMPACT_SOLAR, 4, 1),
                      stack(COMPACT_SOLAR, 2, 2), stack(ADV_MACHINE, 1, 0),
                      stack(ADV_MACHINE, 1, 1), stack(ADV_MACHINE, 1, 2),
                      stack(CHARGING_BENCH, 1, 0), stack(IRON_CHEST, 8, 2)]),
        ("Cells+Batteries", many("itemCellEmpty", 128) + many("itemCellLava", 32)
         + many("itemCellWater", 32) + many("itemBatRE", 16, size=16)
         + [stack("itemBatCrystal", charged=True) for _ in range(4)]
         + [stack("itemBatLamaCrystal", charged=True) for _ in range(2)]
         + many("itemFuelCan", 8, size=1) + many("itemScrap", 256)
         + many("itemScrapbox", 64)),
        ("BuildCraft", [stack(4056, 64), stack(4057, 64), stack(4058, 64), stack(4059, 32),
                        stack(4060, 16), stack(4306, 64), stack(4307, 64), stack(4308, 64),
                        stack(4309, 32), stack(4310, 32), stack(4311, 16), stack(4312, 16),
                        stack(4313, 32), stack(4315, 32), stack(4316, 16), stack(4320, 32),
                        stack(4322, 32), stack(4324, 16), stack(BC_ENGINE, 8, 0),
                        stack(BC_ENGINE, 4, 1), stack(BC_ENGINE, 2, 2), stack(BC_QUARRY, 1),
                        stack(4062, 2), stack(325, 16)]),
        ("RedPower", [stack(1258, 64, 0), stack(1258, 64, 1), stack(1258, 32, 2),
                      stack(1258, 32, 3), stack(1258, 64, 4), stack(1258, 32, 5),
                      stack(1258, 32, 6), stack(1258, 32, 7), stack(1258, 32, 8),
                      stack(1258, 32, 9), stack(1258, 32, 10), stack(1258, 32, 11),
                      stack(1262, 1), stack(1325, 1), stack(1261, 1), stack(1331, 1),
                      stack(1291, 16), stack(147, 64, 0),
                      stack(147, 32, 14), stack(147, 32, 11)]),
        ("Building", many(98, 512) + many(20, 256) + many(5, 256) + many(17, 128)
         + many(RP_STONE, 256, MARBLE_BRICK) + many(RP_STONE, 256, BASALT_BRICK)
         + many(IC_REINF_STONE, 128) + many(IC_REINF_GLASS, 128) + many(49, 64)),
        ("Bulk Stone", many(4, 64 * 30) + many(3, 64 * 10) + many(12, 64 * 8)),
        ("Mob Drops", many(287, 128) + many(288, 64) + many(289, 192) + many(334, 64)
         + many(341, 32) + many(352, 128) + many(367, 64) + many(375, 16)
         + many(368, 32, size=16) + many(370, 8)),
        ("Nether", many(87, 256) + many(88, 128) + many(89, 64) + many(372, 64)
         + many(369, 32) + many(377, 32) + many(378, 16) + many(135, 64, 0)
         + many(135, 32, 1) + many(135, 32, 3)),
        ("Farm", many(296, 256) + many(295, 128) + many(338, 128) + many(361, 32)
         + many(362, 32) + many(81, 64) + many(86, 32) + many(IC_RUB_SAPLING, 64)
         + many(6, 64) + many(351, 128, damage=15) + many("itemFertilizer", 64)),
        ("Alchemy", [stack("philStone"), stack("darkMatter", 64), stack("redMatter", 32),
                     stack("alchemicalCoal", 64), stack("mobiusFuel", 64),
                     stack("aeternalisFuel", 32), stack(EE_STONE, 8, 2),
                     stack(EE_STONE, 4, 7), stack(EE_CHEST, 2, 1), stack(EE_CHEST, 4, 0),
                     stack(EE_STONE, 2, 3), stack(EE_TORCH, 16)]),
        ("Computers", [stack(CC_COMPUTER, 4), stack(CC_DISKDRIVE, 2), stack(4256, 8),
                       stack(208, 1)]),
        ("Wireless+Misc", [stack(6409, 8), stack(6411, 8), stack(6359, 1), stack(6361, 1),
                           stack(7493, 2), stack(178, 4), stack(19757, 4), stack(19758, 4),
                           stack(19762, 2)]),
    ]


# ============================================================= lighting
def relight(w, cx0, cz0, cx1, cz1, ymax=128):
    """Recompute sky light, block light and height maps for a chunk box."""
    nx, nz = (cx1 - cx0 + 1) * 16, (cz1 - cz0 + 1) * 16
    ids = np.zeros((nx, ymax, nz), dtype=np.int32)
    for cx in range(cx0, cx1 + 1):
        for cz in range(cz0, cz1 + 1):
            lv = w.chunk(cx, cz)
            for s in lv["Sections"].value:
                sy = s["Y"].value
                if sy * 16 >= ymax:
                    continue
                blk = np.frombuffer(bytes(s["Blocks"].value), dtype=np.uint8).astype(np.int32)
                if "Add" in s:
                    add = np.frombuffer(bytes(s["Add"].value), dtype=np.uint8)
                    hi = np.empty(4096, dtype=np.int32)
                    hi[0::2] = add & 15
                    hi[1::2] = add >> 4
                    blk = blk | (hi << 8)
                arr = blk.reshape(16, 16, 16)          # [y][z][x]
                ox, oz = (cx - cx0) * 16, (cz - cz0) * 16
                ids[ox:ox + 16, sy * 16:sy * 16 + 16, oz:oz + 16] = arr.transpose(2, 0, 1)
    opa = OPACITY[ids]
    emi = EMISSION[ids]
    att = np.maximum(opa, 1)
    # height map: first block from the top with opacity != 0, plus one
    nonzero = opa > 0
    has = nonzero.any(axis=1)
    top = ymax - np.argmax(nonzero[:, ::-1, :], axis=1)
    height = np.where(has, top, 0)
    ycoord = np.arange(ymax)[None, :, None]
    sky = np.where(ycoord >= height[:, None, :], 15, 0).astype(np.int16)
    blk = emi.astype(np.int16)

    def spread(light, fixed):
        for _ in range(15):
            m = light.copy()
            m[1:] = np.maximum(m[1:], light[:-1])
            m[:-1] = np.maximum(m[:-1], light[1:])
            m[:, 1:] = np.maximum(m[:, 1:], light[:, :-1])
            m[:, :-1] = np.maximum(m[:, :-1], light[:, 1:])
            m[:, :, 1:] = np.maximum(m[:, :, 1:], light[:, :, :-1])
            m[:, :, :-1] = np.maximum(m[:, :, :-1], light[:, :, 1:])
            new = np.maximum(fixed, np.where(opa >= 15, 0, m - att))
            new = np.maximum(new, 0).astype(np.int16)
            if np.array_equal(new, light):
                break
            light = new
        return light

    sky = spread(sky, sky.copy())
    blk = spread(blk, emi.astype(np.int16))

    def nibbles(a):                     # a: [y][z][x] 16^3 -> 2048 bytes
        flat = a.reshape(-1).astype(np.uint8)
        return bytearray((flat[0::2] | (flat[1::2] << 4)).tobytes())

    for cx in range(cx0, cx1 + 1):
        for cz in range(cz0, cz1 + 1):
            lv = w.chunk(cx, cz)
            ox, oz = (cx - cx0) * 16, (cz - cz0) * 16
            for s in lv["Sections"].value:
                sy = s["Y"].value
                if sy * 16 >= ymax:
                    continue
                sl = sky[ox:ox + 16, sy * 16:sy * 16 + 16, oz:oz + 16].transpose(1, 2, 0)
                bl = blk[ox:ox + 16, sy * 16:sy * 16 + 16, oz:oz + 16].transpose(1, 2, 0)
                s["SkyLight"].value = nibbles(sl)
                s["BlockLight"].value = nibbles(bl)
            hm = height[ox:ox + 16, oz:oz + 16].T.reshape(-1)
            lv["HeightMap"].value = [int(v) for v in hm]
            w.dirty.add((cx, cz))


# ================================================================== main
def new_player(x, y, z, yaw=0.0, pitch=0.0):
    """A fresh survival player (empty inventory) standing at x,y,z."""
    from mcworld import Double, TAG_DOUBLE, TAG_FLOAT
    return Compound({
        "Pos": List(TAG_DOUBLE, [Double(x), Double(y), Double(z)]),
        "Motion": List(TAG_DOUBLE, [Double(0), Double(0), Double(0)]),
        "Rotation": List(TAG_FLOAT, [Float(yaw), Float(pitch)]),
        "FallDistance": Float(0), "Fire": Short(-20), "Air": Short(300), "OnGround": Byte(1),
        "Health": Short(20), "HurtTime": Short(0), "DeathTime": Short(0), "AttackTime": Short(0),
        "Inventory": List(TAG_COMPOUND, []), "Dimension": Int(0),
        "Sleeping": Byte(0), "SleepTimer": Short(0),
        "XpP": Float(0), "XpLevel": Int(0), "XpTotal": Int(0),
        "foodLevel": Int(20), "foodTickTimer": Int(0),
        "foodSaturationLevel": Float(5), "foodExhaustionLevel": Float(0),
        "abilities": Compound({"invulnerable": Byte(0), "flying": Byte(0),
                               "mayfly": Byte(0), "instabuild": Byte(0)}),
    })



COMPUTER_STARTUP = r'''-- Base computer: prints a guide to the base
term.clear()
term.setCursorPos(1, 1)
print("========= TEKKIT TECH BASE =========")
print("")
print("FLOOR 1  Machine hall")
print(" - 11 IC2 machines on an LV bus")
print(" - 4x MFSU, MV+LV transformers")
print(" - Mass Fabricator, Induction Furnace")
print(" - Charging Bench, workshop, RP2 tables")
print("FLOOR 2  Storage vault, EE lab, quarters")
print("ROOF     12x HV solar + EMC condenser")
print("OUTSIDE  N: quarry (flip both levers)")
print("         E: reactor bunker (EMPTY!)")
print("         W: wheat farm, rubber trees,")
print("            nether portal")
print("")
print("Type 'edit startup' to change this.")
'''


def main(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
        "session.lock", "players", "railcraft.dat", "EnderStorage", "RedstoneEther", "uid.dat"))
    w = World(dst)

    BX, BZ = 190, 270                     # hall north-west corner
    gs = sorted(ground_height(w, x, z) for x in range(BX, BX + 31, 3) for z in range(BZ, BZ + 23, 3))
    G = gs[len(gs) // 2]
    print("ground level", G)

    b = Builder(w)
    w.remove_entities_in(165, 240, 245, 325)
    prepare_site(b, 168, 248, 240, 322, G)
    build_base(w, BX, BZ, G)
    build_quarry(b, 205, 263, G)
    for z in range(264, 270):              # path north door -> quarry
        b.set(205, G, z, GRAVEL)
    build_reactor(b, 226, 274, G)
    for x in range(222, 226):              # path front -> reactor
        b.set(x, G, 279, GRAVEL)
    for z in range(279, 296):
        b.set(222, G, z, GRAVEL)
    for x in range(207, 222):
        b.set(x, G, 295, GRAVEL)
    build_farm(b, 170, 296, G)
    for x, z in ((178, 286), (172, 289), (176, 283), (181, 290)):
        rubber_tree(b, x, z, G)
    build_portal(b, 182, 300 - 24, G)
    # front path, lamp posts, interdiction torches
    for z in range(BZ + 23, BZ + 40):
        for x in (204, 205, 206):
            b.set(x, G, z, GRAVEL)
    for z in (BZ + 26, BZ + 32, BZ + 38):
        lamp_post(b, 202, z, G)
        lamp_post(b, 208, z, G)
    for x in (203, 207):
        b.set(x, G + 1, BZ + 24, EE_TORCH, 5)
    b.sign(205, G + 1, BZ + 41, SOUTH, ["Tekkit Classic", "TECH BASE", "-> north", ""], wall=False)

    # light + height maps around everything we touched
    cxs = [c[0] for c in w.dirty]
    czs = [c[1] for c in w.dirty]
    relight(w, min(cxs) - 1, min(czs) - 1, max(cxs) + 1, max(czs) + 1)
    w.save()

    # level.dat: name, spawn in front of the hall, morning, clear weather
    name, lvl = load_gz(os.path.join(dst, "level.dat"))
    d = lvl["Data"]
    d["LevelName"] = String("Tekkit Tech Base")
    d["SpawnX"], d["SpawnY"], d["SpawnZ"] = Int(205), Int(G + 1), Int(BZ + 30)
    d["Time"] = Long(1000)
    d["raining"], d["thundering"] = Byte(0), Byte(0)
    d["rainTime"], d["thunderTime"] = Int(180000), Int(250000)
    d["GameType"] = Int(0)
    d["Player"] = new_player(205.5, G + 1, BZ + 30.5, yaw=180.0)
    save_gz(os.path.join(dst, "level.dat"), lvl, name)

    # ComputerCraft: computer #0 runs the base guide on boot
    cdir = os.path.join(dst, "computer", "0")
    os.makedirs(cdir, exist_ok=True)
    with open(os.path.join(cdir, "startup"), "w") as fh:
        fh.write(COMPUTER_STARTUP)
    print("done ->", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
