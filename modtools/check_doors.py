"""Verify: a layout supports a door side iff it has floor at that side's door cell."""
import json, sys
d = json.load(open(sys.argv[1]))
DOOR = {"N": (7, 0), "E": (14, 5), "S": (7, 10), "W": (0, 5)}
def floor(idx):
    return {(round((x - 36) / 52), round((y - 40) / 52)) for c, x, y, _ in d["decal"][str(idx)] if c == "FloorTile"}
bad = ok = 0
for ep, rooms in d["missions"].items():
    cells = {tuple(map(int, k.split(","))) for k, v in rooms.items() if any(e[0] != "propertiesSet" for e in v)}
    for k, ents in rooms.items():
        x, y = map(int, k.split(","))
        dec = [e[1] for e in ents if e[0] == "decalSet"]
        if not dec: continue
        f = floor(dec[0])
        for s, (dx, dy) in {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}.items():
            if (x + dx, y + dy) in cells:
                if DOOR[s] in f: ok += 1
                else: bad += 1; print("missing", ep, k, s, dec[0])
print("ok", ok, "bad", bad)
xs = [i for v in d["decal"].values() for c, x, y, _ in v if c == "FloorTile" for i in [round((x - 36) / 52)]]
ys = [j for v in d["decal"].values() for c, x, y, _ in v if c == "FloorTile" for j in [round((y - 40) / 52)]]
print("col range", min(xs), max(xs), "row range", min(ys), max(ys))
