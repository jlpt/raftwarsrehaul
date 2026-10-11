"""Keep mod_src/ (editable, gitignored) and patches/ (committed) in sync.

The repository is public, so it holds no original game code: every modified class is stored as a
unified diff against the JPEXS decompile in decompiled/scripts/. mod_src/ is rebuilt from those diffs.

Usage: python3 -I modtools/patches.py sync | apply [--force] | make [--force] | status

  sync    what build.sh runs. No mod_src/ yet: apply. Otherwise, if patches/ hasn't changed since
          mod_src/ was last synced: make (mod_src/ is the truth). If both changed: stop and ask.
  apply   rebuild mod_src/ from decompiled/ + patches/ (--force discards local mod_src/ edits).
  make    rewrite patches/ from mod_src/ (--force even if patches/ changed since the last sync).

The generated extra-mission block in LevelGrid.as (see splice_levelgrid.py) is left out of the
patch and re-spliced by build.sh. Diffs are made on LF-normalised text; mod_src/ is written with
CRLF line endings like the JPEXS export.
"""
import difflib, hashlib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEC = os.path.join(ROOT, "decompiled", "scripts")
SRC = os.path.join(ROOT, "mod_src")
PAT = os.path.join(ROOT, "patches")
STAMP = os.path.join(SRC, ".patches_sha1")
SPLICE_MARKER = "      // MOD: extra missions"


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def write(path, text, crlf):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if crlf:
        text = text.replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def unsplice(rel, text):
    if rel.replace(os.sep, "/") == "LevelGridTools/LevelGrid.as" and SPLICE_MARKER in text:
        text = text[: text.index(SPLICE_MARKER)].rstrip() + "\n   }\n}\n"
    return text


def files(base, ext):
    out = []
    for d, _, fs in os.walk(base):
        for f in fs:
            if f.endswith(ext):
                out.append(os.path.relpath(os.path.join(d, f), base))
    return sorted(out)


def patches_hash():
    h = hashlib.sha1()
    if os.path.isdir(PAT):
        for rel in files(PAT, ".patch"):
            h.update(rel.encode() + b"\0" + read(os.path.join(PAT, rel)).encode() + b"\0")
    return h.hexdigest()


def src_hash():
    h = hashlib.sha1()
    if os.path.isdir(SRC):
        for rel in files(SRC, ".as"):
            h.update(rel.encode() + b"\0" + unsplice(rel, read(os.path.join(SRC, rel))).encode() + b"\0")
    return h.hexdigest()


def stamp(save=False):
    """(patches hash, mod_src hash) at the last sync, or (None, None)."""
    if save:
        with open(STAMP, "w") as f:
            f.write(patches_hash() + " " + src_hash() + "\n")
    if not os.path.exists(STAMP):
        return None, None
    return tuple(open(STAMP).read().split())


def changed():
    """(patches/ changed, mod_src/ changed) since the last sync."""
    p, s = stamp()
    return p != patches_hash(), s != src_hash()


def make_patch(rel):
    old = read(os.path.join(DEC, rel)).splitlines(keepends=True)
    new = unsplice(rel, read(os.path.join(SRC, rel))).splitlines(keepends=True)
    name = rel.replace(os.sep, "/")
    return "".join(difflib.unified_diff(old, new, "a/" + name, "b/" + name, n=3))


HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def apply_patch(base_text, patch_text, name):
    src = base_text.splitlines(keepends=True)
    out, pos = [], 0
    lines = patch_text.splitlines(keepends=True)
    i = 0
    while i < len(lines) and not lines[i].startswith("@@"):
        i += 1
    while i < len(lines):
        m = HUNK.match(lines[i])
        if not m:
            raise SystemExit(f"{name}: bad hunk header: {lines[i]!r}")
        start = int(m.group(1)) - (0 if m.group(2) == "0" else 1)
        out += src[pos:start]
        pos = start
        i += 1
        while i < len(lines) and not lines[i].startswith("@@"):
            tag, body = lines[i][0], lines[i][1:]
            if tag == "\\":
                i += 1
                continue
            if tag in " -":
                if pos >= len(src) or src[pos].rstrip("\n") != body.rstrip("\n"):
                    raise SystemExit(f"{name}: patch doesn't match decompiled source at line {pos + 1}")
                if tag == " ":
                    out.append(src[pos])
                pos += 1
            elif tag == "+":
                out.append(body if body.endswith("\n") else body + "\n")
            i += 1
    out += src[pos:]
    return "".join(out)


def built_from_patches():
    res = {}
    for prel in files(PAT, ".patch"):
        rel = prel[: -len(".patch")]
        res[rel] = apply_patch(read(os.path.join(DEC, rel)), read(os.path.join(PAT, prel)), prel)
    return res


def cmd_apply(force):
    if not os.path.isdir(DEC):
        raise SystemExit("decompiled/scripts is missing: run ./build.sh (it decompiles original/robokill.swf)")
    if os.path.isdir(SRC) and not force and changed()[1]:
        raise SystemExit("mod_src/ has edits that aren't in patches/ yet. Run `patches.py make` first, "
                         "or `apply --force` to discard them.")
    new = built_from_patches()
    for rel in files(SRC, ".as") if os.path.isdir(SRC) else []:
        if rel not in new:
            os.remove(os.path.join(SRC, rel))
    for rel, text in new.items():
        write(os.path.join(SRC, rel), text, crlf=True)
    stamp(save=True)
    print(f"mod_src/: {len(new)} classes rebuilt from patches/")


def cmd_make(force):
    if not force and changed()[0]:
        raise SystemExit("patches/ changed since mod_src/ was last synced (git pull?). Run `patches.py apply` "
                         "to rebuild mod_src/ from it, or `make --force` to overwrite patches/ with mod_src/.")
    keep = set()
    for rel in files(SRC, ".as"):
        if not os.path.exists(os.path.join(DEC, rel)):
            raise SystemExit(f"mod_src/{rel}: no such class in the original game (only existing classes can be replaced)")
        p = make_patch(rel)
        if p:
            write(os.path.join(PAT, rel + ".patch"), p, crlf=False)
            keep.add(rel + ".patch")
    for rel in files(PAT, ".patch"):
        if rel not in keep:
            os.remove(os.path.join(PAT, rel))
    stamp(save=True)
    print(f"patches/: {len(keep)} patches written from mod_src/")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    force = "--force" in sys.argv
    if cmd == "apply":
        cmd_apply(force)
    elif cmd == "make":
        cmd_make(force)
    elif cmd == "sync":
        p_changed, s_changed = changed()
        if not os.path.isdir(SRC) or not files(SRC, ".as"):
            cmd_apply(True)
        elif stamp()[0] is None:
            cmd_make(True)  # existing mod_src/ from before patches/ existed: it is the truth
        elif p_changed and s_changed:
            raise SystemExit("Both patches/ (git pull?) and mod_src/ changed since the last sync. Keep one: "
                             "`patches.py apply --force` (patches win) or `patches.py make --force` (mod_src wins).")
        elif p_changed:
            cmd_apply(True)
        elif s_changed:
            cmd_make(True)
        else:
            print("mod_src/ and patches/ in sync")
    elif cmd == "status":
        print("patches changed: %s, mod_src changed: %s" % changed())
    else:
        raise SystemExit(__doc__)


main()
