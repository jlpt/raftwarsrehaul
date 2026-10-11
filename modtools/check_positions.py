import json, sys, collections
d = json.load(open(sys.argv[1]))
base = {int(k): v[0] for k, v in d["default"].items()}
def floor(idx):
    return {(round((x - 36) / 52), round((y - 40) / 52)) for c, x, y, _ in d["decal"][str(idx)] if c == "FloorTile"}
on = collections.Counter(); tot = collections.Counter(); offs = collections.Counter()
for ep, rooms in d["missions"].items():
    for k, ents in rooms.items():
        dec = [e[1] for e in ents if e[0] == "decalSet"]
        if not dec: continue
        f = floor(dec[0])
        for s, i, fx, fy in ents:
            if s != "defaultSet": continue
            c, bx, by, _ = base[i]
            px, py = bx + 780 * (fx - 0.5), by + 572 * (fy - 0.5)
            cell = (round((px - 36) / 52), round((py - 40) / 52))
            tot[c] += 1; on[c] += cell in f
            offs[(round((px - 36) % 52), round((py - 40) % 52))] += 1
for c in sorted(tot, key=lambda c: -tot[c]):
    print(f"{c:15s} {on[c]:4d}/{tot[c]:4d} on floor")
print("most common sub-cell offsets:", offs.most_common(5))
