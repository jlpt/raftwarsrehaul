import json, sys, collections
d = json.load(open(sys.argv[1]))
names = {int(k): v[0][0] for k, v in d["default"].items() if v}
props = collections.Counter(); doorsets = collections.defaultdict(set); usage = collections.Counter()
per_ep = {}
for ep, rooms in sorted(d["missions"].items(), key=lambda t: int(t[0])):
    cells = {tuple(map(int, k.split(","))) for k, v in rooms.items() if any(e[0] != "propertiesSet" for e in v)}
    enemies = []
    for k, ents in rooms.items():
        x, y = map(int, k.split(","))
        dec = [e for e in ents if e[0] == "decalSet"]
        if not dec: continue
        sides = frozenset(s for s, (dx, dy) in {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}.items() if (x + dx, y + dy) in cells)
        doorsets[dec[0][1]].add(sides); usage[dec[0][1]] += 1
        ps = [e[1] for e in ents if e[0] == "propertiesSet"]
        for p in ps: props[p] += 1
        objs = [names.get(e[1], "?") for e in ents if e[0] == "defaultSet"]
        enemies.append(len(objs))
        if ps and ep in ("0", "12"):
            print(f"ep{ep} {k} props={ps} decal={dec[0][1]} objs={objs}")
    per_ep[ep] = (len(cells), round(sum(enemies) / max(1, len(enemies)), 1))
print("props usage:", props)
print("rooms / avg objects per room:", per_ep)
print("layouts used:", len(usage))
# layouts by available sides (union of observed)
full = [k for k, s in doorsets.items() if frozenset("NESW") <= frozenset().union(*s)]
print("layouts seen with all 4 sides:", len(full))
