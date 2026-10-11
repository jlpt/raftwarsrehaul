"""Insert the extra-mission block into LevelGrid.as (idempotent).

Usage: python3 -I splice_levelgrid.py LevelGrid.as levelgrid_extra.as.tmpl extra_missions.as
"""
import sys

target, tmpl, data = sys.argv[1:4]
src = open(target).read()
marker = "      // MOD: extra missions"
if marker in src:
    src = src[: src.index(marker)].rstrip() + "\n   }\n}\n"
block = open(tmpl).read().replace("@@MISSION_DATA@@", open(data).read().rstrip("\n"))
# insert before the closing braces of the class and package
head = src.rstrip()
assert head.endswith("}") and head[:-1].rstrip().endswith("}")
class_end = head[:-1].rstrip()[:-1].rstrip()
open(target, "w").write(class_end + "\n" + block + "   }\n}\n")
print("spliced", target)
