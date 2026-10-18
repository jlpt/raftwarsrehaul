"""Minimal NBT + Anvil (.mca) reader/writer for Minecraft 1.2.5 worlds.

Tekkit Classic runs Minecraft 1.2.5, which already uses the Anvil region
format (16x16x16 sections, YZX block order, optional "Add" nibbles for
block IDs above 255).
"""
import gzip
import io
import os
import struct
import zlib

# ---------------------------------------------------------------- NBT tags
TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG, TAG_FLOAT, TAG_DOUBLE, \
    TAG_BYTE_ARRAY, TAG_STRING, TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY = range(12)


class Tag:
    __slots__ = ("type", "value", "list_type")

    def __init__(self, type_, value, list_type=TAG_END):
        self.type = type_
        self.value = value
        self.list_type = list_type

    def __repr__(self):
        return "Tag(%d, %r)" % (self.type, self.value)

    # convenience for compounds
    def __getitem__(self, k):
        return self.value[k]

    def __setitem__(self, k, v):
        self.value[k] = v

    def __contains__(self, k):
        return k in self.value

    def get(self, k, default=None):
        return self.value.get(k, default)


def Byte(v): return Tag(TAG_BYTE, int(v))
def Short(v): return Tag(TAG_SHORT, int(v))
def Int(v): return Tag(TAG_INT, int(v))
def Long(v): return Tag(TAG_LONG, int(v))
def Float(v): return Tag(TAG_FLOAT, float(v))
def Double(v): return Tag(TAG_DOUBLE, float(v))
def String(v): return Tag(TAG_STRING, str(v))
def ByteArray(v): return Tag(TAG_BYTE_ARRAY, bytearray(v))
def IntArray(v): return Tag(TAG_INT_ARRAY, list(v))


def Compound(d=None):
    return Tag(TAG_COMPOUND, dict(d or {}))


def List(list_type, items=()):
    return Tag(TAG_LIST, list(items), list_type)


def _read_payload(t, f):
    if t == TAG_BYTE:
        return struct.unpack(">b", f.read(1))[0]
    if t == TAG_SHORT:
        return struct.unpack(">h", f.read(2))[0]
    if t == TAG_INT:
        return struct.unpack(">i", f.read(4))[0]
    if t == TAG_LONG:
        return struct.unpack(">q", f.read(8))[0]
    if t == TAG_FLOAT:
        return struct.unpack(">f", f.read(4))[0]
    if t == TAG_DOUBLE:
        return struct.unpack(">d", f.read(8))[0]
    if t == TAG_BYTE_ARRAY:
        n = struct.unpack(">i", f.read(4))[0]
        return bytearray(f.read(n))
    if t == TAG_STRING:
        n = struct.unpack(">H", f.read(2))[0]
        return f.read(n).decode("utf-8")
    if t == TAG_INT_ARRAY:
        n = struct.unpack(">i", f.read(4))[0]
        return list(struct.unpack(">%di" % n, f.read(4 * n)))
    raise ValueError(t)


def _read_tag(t, f):
    if t == TAG_LIST:
        lt = f.read(1)[0]
        n = struct.unpack(">i", f.read(4))[0]
        return Tag(TAG_LIST, [_read_tag(lt, f) for _ in range(n)], lt)
    if t == TAG_COMPOUND:
        d = {}
        while True:
            ct = f.read(1)[0]
            if ct == TAG_END:
                break
            n = struct.unpack(">H", f.read(2))[0]
            name = f.read(n).decode("utf-8")
            d[name] = _read_tag(ct, f)
        return Tag(TAG_COMPOUND, d)
    return Tag(t, _read_payload(t, f))


def _write_tag(tag, f):
    t, v = tag.type, tag.value
    if t == TAG_BYTE:
        f.write(struct.pack(">b", v))
    elif t == TAG_SHORT:
        f.write(struct.pack(">h", v))
    elif t == TAG_INT:
        f.write(struct.pack(">i", v))
    elif t == TAG_LONG:
        f.write(struct.pack(">q", v))
    elif t == TAG_FLOAT:
        f.write(struct.pack(">f", v))
    elif t == TAG_DOUBLE:
        f.write(struct.pack(">d", v))
    elif t == TAG_BYTE_ARRAY:
        f.write(struct.pack(">i", len(v)))
        f.write(bytes(v))
    elif t == TAG_STRING:
        b = v.encode("utf-8")
        f.write(struct.pack(">H", len(b)))
        f.write(b)
    elif t == TAG_INT_ARRAY:
        f.write(struct.pack(">i", len(v)))
        f.write(struct.pack(">%di" % len(v), *v))
    elif t == TAG_LIST:
        lt = tag.list_type
        if v and lt == TAG_END:
            lt = v[0].type
        f.write(bytes([lt]))
        f.write(struct.pack(">i", len(v)))
        for item in v:
            _write_tag(item, f)
    elif t == TAG_COMPOUND:
        for name, child in v.items():
            f.write(bytes([child.type]))
            b = name.encode("utf-8")
            f.write(struct.pack(">H", len(b)))
            f.write(b)
            _write_tag(child, f)
        f.write(bytes([TAG_END]))
    else:
        raise ValueError(t)


def read_nbt(data):
    f = io.BytesIO(data)
    t = f.read(1)[0]
    n = struct.unpack(">H", f.read(2))[0]
    name = f.read(n).decode("utf-8")
    return name, _read_tag(t, f)


def write_nbt(tag, name=""):
    f = io.BytesIO()
    f.write(bytes([tag.type]))
    b = name.encode("utf-8")
    f.write(struct.pack(">H", len(b)))
    f.write(b)
    _write_tag(tag, f)
    return f.getvalue()


def load_gz(path):
    with gzip.open(path, "rb") as fh:
        return read_nbt(fh.read())


def save_gz(path, tag, name=""):
    raw = write_nbt(tag, name)
    with open(path, "wb") as fh:
        fh.write(gzip.compress(raw))


# ------------------------------------------------------------ Anvil regions
class Region:
    def __init__(self, path):
        self.path = path
        self.chunks = {}   # (lx, lz) -> (timestamp, Tag)
        if os.path.exists(path):
            self._load()

    def _load(self):
        with open(self.path, "rb") as fh:
            data = fh.read()
        if len(data) < 8192:
            return
        for i in range(1024):
            off = struct.unpack(">I", data[i * 4:i * 4 + 4])[0]
            ts = struct.unpack(">I", data[4096 + i * 4:4096 + i * 4 + 4])[0]
            sector, count = off >> 8, off & 0xFF
            if sector == 0 or count == 0:
                continue
            p = sector * 4096
            length = struct.unpack(">I", data[p:p + 4])[0]
            comp = data[p + 4]
            payload = data[p + 5:p + 4 + length]
            if comp == 2:
                raw = zlib.decompress(payload)
            elif comp == 1:
                raw = gzip.decompress(payload)
            else:
                raise ValueError("unknown compression %d" % comp)
            self.chunks[(i % 32, i // 32)] = (ts, read_nbt(raw)[1])

    def save(self):
        header = bytearray(8192)
        body = bytearray()
        sector = 2
        for i in range(1024):
            key = (i % 32, i // 32)
            if key not in self.chunks:
                continue
            ts, tag = self.chunks[key]
            payload = zlib.compress(write_nbt(tag), 6)
            blob = struct.pack(">IB", len(payload) + 1, 2) + payload
            pad = (-len(blob)) % 4096
            blob += b"\0" * pad
            n = len(blob) // 4096
            struct.pack_into(">I", header, i * 4, (sector << 8) | n)
            struct.pack_into(">I", header, 4096 + i * 4, ts)
            body += blob
            sector += n
        with open(self.path, "wb") as fh:
            fh.write(header + body)


class World:
    """Block-level editing on top of Anvil region files."""

    def __init__(self, path):
        self.path = path
        self.regions = {}
        self.dirty = set()

    def region(self, rx, rz):
        key = (rx, rz)
        if key not in self.regions:
            self.regions[key] = Region(os.path.join(self.path, "region", "r.%d.%d.mca" % (rx, rz)))
        return self.regions[key]

    def chunk(self, cx, cz):
        r = self.region(cx >> 5, cz >> 5)
        entry = r.chunks.get((cx & 31, cz & 31))
        if entry is None:
            return None
        return entry[1]["Level"]

    def has_chunk(self, cx, cz):
        return self.chunk(cx, cz) is not None

    def _section(self, level, sy, create):
        secs = level["Sections"].value
        for s in secs:
            if s["Y"].value == sy:
                return s
        if not create:
            return None
        s = Compound({
            "Y": Byte(sy),
            "Blocks": ByteArray(bytes(4096)),
            "Data": ByteArray(bytes(2048)),
            "SkyLight": ByteArray(b"\xff" * 2048),
            "BlockLight": ByteArray(bytes(2048)),
        })
        secs.append(s)
        level["Sections"].list_type = TAG_COMPOUND
        return s

    def get(self, x, y, z):
        if y < 0 or y > 255:
            return 0, 0
        level = self.chunk(x >> 4, z >> 4)
        if level is None:
            return None
        s = self._section(level, y >> 4, False)
        if s is None:
            return 0, 0
        i = ((y & 15) << 8) | ((z & 15) << 4) | (x & 15)
        bid = s["Blocks"].value[i]
        if "Add" in s:
            a = s["Add"].value[i >> 1]
            bid |= ((a >> 4) if i & 1 else (a & 15)) << 8
        d = s["Data"].value[i >> 1]
        meta = (d >> 4) if i & 1 else (d & 15)
        return bid, meta

    def set(self, x, y, z, bid, meta=0):
        if y < 0 or y > 255:
            return
        cx, cz = x >> 4, z >> 4
        level = self.chunk(cx, cz)
        if level is None:
            raise KeyError("chunk %d,%d not generated" % (cx, cz))
        s = self._section(level, y >> 4, bid != 0)
        if s is None:
            return
        i = ((y & 15) << 8) | ((z & 15) << 4) | (x & 15)
        s["Blocks"].value[i] = bid & 255
        if bid > 255 or "Add" in s:
            if "Add" not in s:
                s["Add"] = ByteArray(bytes(2048))
            a = s["Add"].value
            hi = (bid >> 8) & 15
            if i & 1:
                a[i >> 1] = (a[i >> 1] & 0x0F) | (hi << 4)
            else:
                a[i >> 1] = (a[i >> 1] & 0xF0) | hi
        dv = s["Data"].value
        if i & 1:
            dv[i >> 1] = (dv[i >> 1] & 0x0F) | ((meta & 15) << 4)
        else:
            dv[i >> 1] = (dv[i >> 1] & 0xF0) | (meta & 15)
        self.dirty.add((cx, cz))

    # tile entities ------------------------------------------------------
    def remove_tile(self, x, y, z):
        level = self.chunk(x >> 4, z >> 4)
        tl = level["TileEntities"]
        tl.value = [t for t in tl.value
                    if not (t["x"].value == x and t["y"].value == y and t["z"].value == z)]
        self.dirty.add((x >> 4, z >> 4))

    def add_tile(self, x, y, z, te_id, fields=None):
        self.remove_tile(x, y, z)
        level = self.chunk(x >> 4, z >> 4)
        tag = Compound({"id": String(te_id), "x": Int(x), "y": Int(y), "z": Int(z)})
        for k, v in (fields or {}).items():
            tag[k] = v
        level["TileEntities"].value.append(tag)
        level["TileEntities"].list_type = TAG_COMPOUND
        return tag

    def remove_entities_in(self, x0, z0, x1, z1):
        for cx in range(x0 >> 4, (x1 >> 4) + 1):
            for cz in range(z0 >> 4, (z1 >> 4) + 1):
                level = self.chunk(cx, cz)
                if level is None:
                    continue
                ents = level["Entities"]
                keep = []
                for e in ents.value:
                    px, _, pz = (p.value for p in e["Pos"].value)
                    if x0 <= px <= x1 + 1 and z0 <= pz <= z1 + 1:
                        continue
                    keep.append(e)
                ents.value = keep
                self.dirty.add((cx, cz))

    def save(self):
        for (cx, cz) in self.dirty:
            r = self.region(cx >> 5, cz >> 5)
            ts, tag = r.chunks[(cx & 31, cz & 31)]
            r.chunks[(cx & 31, cz & 31)] = (ts, tag)
        touched = {(cx >> 5, cz >> 5) for (cx, cz) in self.dirty}
        for key in touched:
            self.regions[key].save()
        self.dirty.clear()
