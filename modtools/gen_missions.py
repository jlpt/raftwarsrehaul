"""Generate extra Robokill missions as AS3 data for LevelGrid.

Usage: python3 -I gen_missions.py levels.json out.as

Each mission is a fresh map (random-walk main path + side branches), with
locked treasure rooms, keys, a gated finish room, checkpoints, a shop at the
start, and enemy groups drawn from a per-mission pool. Room floor shapes are
picked from the game's existing floor layouts so walls/doors render properly.
"""
import json, random, sys

d = json.load(open(sys.argv[1]))
OUT = sys.argv[2]

BASE = {int(k): v[0] for k, v in d["default"].items()}
DOOR = {"N": (7, 0), "E": (14, 5), "S": (7, 10), "W": (0, 5)}
DIRS = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
HAZARDS = {"FlameThrowerTile", "LaserTile", "Fan"}

# defaultSet indices
START_MARK, KEY_LOCK, FINISH_MARK, CHECKPOINT_MARK, AMBUSH_MARK = 0, 1, 3, 5, 6
OBJ = dict(Hulk=0, Charge=1, Spawn=2, Grunt=4, TreasureChest=5, Cash=6, KeyPlace=10, Turret=11,
           Spider=12, Swarm=13, Hover=14, SpiderGunner=15, GunFighter=25, BigTurret=26,
           ShootingGrunt=27, RespawnPoint=28, BigFlyBot=29, SpiderSpit=30, Walker=32,
           MineLayer=33, Sleeper=34, HoverSwarm=35, Inertia=36, HoverSpawn=37, Beserker=38,
           ShopTile=39, Jumper=41, HoverSwarm2=42, HoverSwarmGun=43, Boss=44)
for name, idx in OBJ.items():
    assert BASE[idx][0].split(".")[-1] == name, (name, BASE[idx])

# enemy variants (EnemyBase.V_*): host enemy and variant number; stored as host index + 1000 x variant,
# which MainScene.initLevel decodes
VARIANTS = dict(Sniper=("Turret", 1), Bomber=("Hover", 2), Bulwark=("Hulk", 3), Brood=("Spider", 4),
                Kamikaze=("Charge", 5), Warden=("GunFighter", 6))


def obj_code(obj):
    if obj in VARIANTS:
        host, v = VARIANTS[obj]
        return OBJ[host] + 1000 * v
    return OBJ[obj]


def host_of(obj):
    return VARIANTS[obj][0] if obj in VARIANTS else obj

# threat cost of each enemy, and whether it needs a clear 3x3 footprint
COST = dict(Charge=1.6, Swarm=0.5, Jumper=0.6, HoverSwarm2=0.7, HoverSwarm=0.8, Grunt=1, ShootingGrunt=1.4,
            Spider=1.4, Turret=1.5, SpiderGunner=1.8, Hover=1.8, MineLayer=2, Spawn=2.2,
            HoverSwarmGun=2, Sleeper=2.4, SpiderSpit=2.6, Hulk=3, BigTurret=3, BigFlyBot=3,
            Inertia=3, GunFighter=4, HoverSpawn=4, Walker=4.5, Beserker=6,
            Sniper=2, Bomber=2.2, Bulwark=3.5, Brood=2, Kamikaze=1.8, Warden=7)
BIG = {"Hulk", "BigTurret", "BigFlyBot", "Inertia", "GunFighter", "HoverSpawn", "Walker", "Beserker",
       "Bulwark", "Warden"}
HUGE = {"Boss"}  # needs a clear 5x5 area

MISSIONS = [
    # ep, rooms, main path length, locked chest rooms, room threat budget, enemy pool, finish guards
    dict(ep=13, seed=1401, rooms=30, main=13, chests=2, budget=(8, 12),
         pool=dict(Grunt=3, ShootingGrunt=3, Spider=2, SpiderGunner=2, Swarm=2, Spawn=2, Hulk=1.5,
                   Turret=1.5, Hover=1, MineLayer=1, Jumper=1, Charge=1),
         guards=["Warden", "Hulk", "BigTurret", "ShootingGrunt", "Sniper", "Spawn"]),
    dict(ep=14, seed=1502, rooms=34, main=14, chests=3, budget=(8, 12),
         pool=dict(Swarm=3, HoverSwarm=2, HoverSwarm2=2, Jumper=3, Spider=2, SpiderSpit=1.5, Spawn=2,
                   HoverSpawn=0.8, Sleeper=1.5, Hover=1.5, SpiderGunner=1.5, Inertia=1),
         guards=["HoverSpawn", "Brood", "SpiderSpit", "Sleeper", "Kamikaze", "Kamikaze", "Jumper"]),
    dict(ep=15, seed=1603, rooms=36, main=15, chests=3, budget=(10, 14),
         pool=dict(Turret=2, BigTurret=1.5, GunFighter=1, MineLayer=2.5, Sleeper=2, ShootingGrunt=2.5,
                   Walker=0.7, BigFlyBot=1.2, Hulk=1.5, SpiderGunner=1.5, HoverSwarmGun=1.5, Inertia=1),
         guards=["Warden", "Walker", "Bulwark", "MineLayer", "Sniper", "HoverSwarmGun"]),
    dict(ep=16, seed=1704, rooms=40, main=16, chests=4, budget=(11, 16),
         pool=dict(Beserker=0.4, GunFighter=1.2, Walker=0.6, Inertia=1.5, BigFlyBot=1.5, Sleeper=1.5,
                   MineLayer=1.5, HoverSpawn=0.7, SpiderSpit=1.2, ShootingGrunt=2, Jumper=2, Hulk=1.5,
                   HoverSwarmGun=1.5, BigTurret=1, Spawn=1.5),
         guards=["Boss", "Warden", "Bulwark"]),
]


def layout_info(idx):
    ents = d["decal"][str(idx)]
    cell = lambda x, y: (round((x - 36) / 52), round((y - 40) / 52))
    floor = {cell(x, y) for c, x, y, _ in ents if c == "FloorTile"}
    blocked = {cell(x, y) for c, x, y, _ in ents if c in HAZARDS or c == "FloorProp"}
    special = any(c in ("Shuttle",) for c, *_ in ents)
    return floor, blocked, special


# Layouts that the original missions actually use, minus special ones (boss arena, shuttle bays)
used = {}
for ep, rooms in d["missions"].items():
    for ents in rooms.values():
        for s, i, *_ in ents:
            if s == "decalSet":
                used.setdefault(i, set()).add(int(ep))
start_layouts = {e[1] for rooms in d["missions"].values() for ents in rooms.values()
                 if any(x[0] == "propertiesSet" and x[1] == START_MARK for x in ents)
                 for e in ents if e[0] == "decalSet"}
LAYOUTS = {}
for idx in used:
    floor, blocked, special = layout_info(idx)
    if special or idx == 162 or len(floor - blocked) < 30:
        continue
    LAYOUTS[idx] = (floor, blocked, frozenset(s for s, c in DOOR.items() if c in floor))


def grow_map(rng, m):
    """Return (cells, start, finish, lock_room, chest_rooms) or None if the attempt failed."""
    start = (0, 0)
    main = [start]
    heading = rng.choice(list(DIRS))
    while len(main) < m["main"]:
        x, y = main[-1]
        opts = []
        for dname, (dx, dy) in DIRS.items():
            c = (x + dx, y + dy)
            if c in main:
                continue
            touching = sum((c[0] + ax, c[1] + ay) in main for ax, ay in DIRS.values())
            if touching > 1:
                continue
            opts += [c] * (3 if dname == heading else 1)
        if not opts:
            return None
        nxt = rng.choice(opts)
        heading = [k for k, v in DIRS.items() if v == (nxt[0] - x, nxt[1] - y)][0]
        main.append(nxt)
    cells = set(main)
    finish, lock_room = main[-1], main[-2]
    nbrs = lambda c: [(c[0] + dx, c[1] + dy) for dx, dy in DIRS.values()]
    forbidden = set(nbrs(finish))  # finish must only connect through the locked room

    def free(c):
        return c not in cells and c not in forbidden and c != finish

    # side branches
    tries = 0
    while len(cells) < m["rooms"] - m["chests"] and tries < 2000:
        tries += 1
        root = rng.choice([c for c in cells if c not in (finish, lock_room)])
        length = rng.randint(1, 4)
        cur = root
        for _ in range(length):
            opts = [c for c in nbrs(cur) if free(c)]
            if not opts or len(cells) >= m["rooms"] - m["chests"]:
                break
            cur = rng.choice(opts)
            cells.add(cur)
    # locked treasure rooms: dead ends touching exactly one ordinary room
    chest_rooms = []
    tries = 0
    while len(chest_rooms) < m["chests"] and tries < 2000:
        tries += 1
        root = rng.choice([c for c in cells if c not in (finish, lock_room, start) and c not in chest_rooms])
        opts = [c for c in nbrs(root) if free(c) and sum(n in cells for n in nbrs(c)) == 1]
        if opts:
            c = rng.choice(opts)
            cells.add(c)
            chest_rooms.append(c)
            forbidden.update(nbrs(c))
    if len(chest_rooms) < m["chests"] or len(cells) < m["rooms"]:
        return None
    # the finish has to be reachable only via lock_room
    if [n for n in nbrs(finish) if n in cells] != [lock_room]:
        return None
    return cells, start, finish, lock_room, chest_rooms


def sides_of(cells, c):
    return frozenset(s for s, (dx, dy) in DIRS.items() if (c[0] + dx, c[1] + dy) in cells)


def to_frac(obj, cx, cy):
    """Convert a floor cell to the level-editor fractional coords used by defaultSet."""
    _, bx, by, _ = BASE[OBJ[host_of(obj)]]
    px, py = 36 + 52 * cx, 40 + 52 * cy
    return round((px - bx) / 780 + 0.5, 6), round((py - by) / 572 + 0.5, 6)


class Room:
    def __init__(self, rng, layout, sides):
        self.rng = rng
        self.layout = layout
        floor, blocked, _ = LAYOUTS[layout]
        self.floor = floor
        door_cells = [DOOR[s] for s in sides]
        self.free = {c for c in floor - blocked
                     if all(max(abs(c[0] - dx), abs(c[1] - dy)) > 2 for dx, dy in door_cells)}
        self.objects = []
        self.marks = []

    def take(self, obj, big=False, near=None, spacing=2):
        r = 2 if obj in HUGE else (1 if big else 0)
        cands = [c for c in self.free
                 if all((c[0] + dx, c[1] + dy) in self.floor for dx in range(-r, r + 1) for dy in range(-r, r + 1))]
        if near:
            cands.sort(key=lambda c: abs(c[0] - near[0]) + abs(c[1] - near[1]))
            cands = cands[:3]
        if not cands:
            return False
        c = self.rng.choice(cands)
        self.objects.append((obj_code(obj), *to_frac(obj, *c)))
        r = max(spacing - 1, 2 if obj in HUGE else 0)
        self.free -= {(c[0] + dx, c[1] + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)}
        self.free.discard(c)
        return True

    def enemies(self, pool, budget):
        names, weights = zip(*pool.items())
        spent = 0
        while spent < budget:
            e = self.rng.choices(names, weights)[0]
            if spent + COST[e] > budget + 1:
                if COST[e] > 1.5:
                    continue
                break
            group = 1
            if COST[e] <= 0.8:  # small fry come in packs
                group = self.rng.randint(2, 4)
            for _ in range(group):
                if not self.take(e, big=e in BIG, spacing=1 if COST[e] <= 0.8 else 2):
                    return
                spent += COST[e]


def build(m):
    rng = random.Random(m["seed"])
    while True:
        res = grow_map(rng, m)
        if res:
            break
    cells, start, finish, lock_room, chest_rooms = res
    ordinary = [c for c in cells if c not in (start, finish, lock_room, *chest_rooms)]
    rng.shuffle(ordinary)
    key_rooms = set(ordinary[: 1 + len(chest_rooms)])
    checkpoints = set(ordinary[len(key_rooms): len(key_rooms) + max(3, len(cells) // 6)])
    ambush = set(rng.sample([c for c in ordinary if c not in key_rooms], k=max(2, len(cells) // 10)))
    shop2 = rng.choice(sorted(checkpoints))

    recent = []
    rooms = {}
    for c in sorted(cells):
        sides = sides_of(cells, c)
        pool_ids = [i for i, (_, _, s) in LAYOUTS.items() if sides <= s]
        if c == start:
            pref = [i for i in pool_ids if i in start_layouts]
            pool_ids = pref or pool_ids
        fresh = [i for i in pool_ids if i not in recent] or pool_ids
        layout = rng.choice(fresh)
        recent = (recent + [layout])[-25:]
        room = Room(rng, layout, sides)
        if c == start:
            room.marks.append(START_MARK)
            room.take("RespawnPoint", near=(7, 5))
            room.take("ShopTile", near=(7, 5))
        elif c == finish:
            room.marks.append(FINISH_MARK)
            for g in m["guards"]:
                room.take(g, big=g in BIG)
            room.take("TreasureChest")
        elif c in chest_rooms:
            room.marks.append(KEY_LOCK)
            room.take("TreasureChest", near=(7, 5))
            if rng.random() < 0.5:
                room.take("TreasureChest", near=(7, 5))
            room.take("Cash")
            room.enemies(m["pool"], m["budget"][0] * 0.6)
        else:
            if c == lock_room:
                room.marks.append(KEY_LOCK)
            if c in checkpoints:
                room.marks.append(CHECKPOINT_MARK)
                room.take("RespawnPoint", near=(7, 5))
                if c == shop2:
                    room.take("ShopTile", near=(7, 5))
            if c in key_rooms:
                room.take("KeyPlace")
            if c in ambush:
                room.marks.append(AMBUSH_MARK)
            if rng.random() < 0.3:
                room.take("Cash")
            lo, hi = m["budget"]
            room.enemies(m["pool"], rng.uniform(lo, hi) * (1.3 if c == lock_room else 1))
        rooms[c] = room
    return rooms, dict(start=start, finish=finish, lock=lock_room, chests=chest_rooms,
                       keys=sorted(key_rooms), checkpoints=sorted(checkpoints))


def fmt(v):
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


lines = []
summary = []
for m in MISSIONS:
    rooms, info = build(m)
    enemy_count = sum(1 for r in rooms.values() for o in r.objects
                      if BASE[o[0] % 1000][0].split(".")[-1] in COST)
    summary.append(f"mission {m['ep'] + 1}: {len(rooms)} rooms, {enemy_count} enemies, "
                   f"{len(info['chests'])} locked chest rooms, keys {len(info['keys'])}")
    parts = []
    for (x, y), r in sorted(rooms.items()):
        objs = ",".join(f"{o[0]},{fmt(o[1])},{fmt(o[2])}" for o in r.objects)
        marks = ",".join(str(k) for k in r.marks)
        parts.append(f"[{x},{y},{r.layout},[{marks}],[{objs}]]")
    lines.append(f"         EXTRA_MISSIONS[{m['ep']}] = [\n            " + ",\n            ".join(parts) + "];")

open(OUT, "w").write("\n".join(lines) + "\n")
print("\n".join(summary))
