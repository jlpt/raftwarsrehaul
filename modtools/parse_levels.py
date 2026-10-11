"""Parse decompiled Robokill level data into JSON for the mission generator."""
import json, re, sys

SRC = sys.argv[1]  # decompiled/scripts dir
OUT = sys.argv[2]

def read(p):
    with open(f"{SRC}/{p}", encoding="utf-8") as f:
        return f.read()

def parse_set(text):
    """Return {index: [[ClassName, x, y, extra], ...]} from a *Set.as file."""
    funcs = {}
    for m in re.finditer(r"internal function createLevel(\d+)\(.*?var _loc3_:Array = (\[.*?\]);\s*\n", text, re.S):
        idx = int(m.group(1))
        items = re.findall(r"\[([A-Za-z_.0-9]+),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\]", m.group(2))
        funcs[idx] = [[c, float(x), float(y), float(e)] for c, x, y, e in items]
    return funcs

decal = parse_set(read("Levels/decalSet.as"))
default = parse_set(read("Levels/defaultSet.as"))

# mainGameLevels: episode -> {(x,y): [[set, idx, fx, fy], ...]}
mgl = read("Levels/mainGameLevels.as")
init_body = mgl[: mgl.index("public static function maxX")]
missions = {}
ep = None
for line in init_body.splitlines():
    m = re.match(r"\s*if\(param1 == (\d+)\)", line)
    if m:
        ep = int(m.group(1)); continue
    m = re.match(r"\s*if\(param2 == (-?\d+) && param3 == (-?\d+)\)", line)
    if m:
        cur = (int(m.group(1)), int(m.group(2))); continue
    m = re.match(r"\s*return (\[\[.*\]\]);", line)
    if m and ep is not None:
        ents = re.findall(r"\[new (\w+)\(\),(-?\d+),(-?[\d.e-]+),(-?[\d.e-]+)\]", m.group(1))
        missions.setdefault(ep, {})[f"{cur[0]},{cur[1]}"] = [[s, int(i), float(x), float(y)] for s, i, x, y in ents]

json.dump({"decal": decal, "default": default, "missions": missions}, open(OUT, "w"))
print("decal layouts:", len(decal), "default objs:", len(default), "missions:", sorted(missions))
