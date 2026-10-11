"""Render enemy sprites with each tier's colour matrix (same maths as EnemyBase.tintClip)."""
import math, sys
from PIL import Image, ImageDraw
sprites = sys.argv[2:]
out = sys.argv[1]
def rainbow(theta):
    c, s = math.cos(theta), math.sin(theta) / math.sqrt(3)
    return (1.15 * (1 + 2 * c) / 3, 1.15 * ((1 - c) / 3 - s), 1.15 * ((1 - c) / 3 + s))
tiers = [("green", (0, 0.21, 0.79)), ("blue", (0, 0.89, 0.31)), ("red", (1, 0, 0)), ("yellow", (1.18, -0.54, 0.61)),
         ("PURPLE", (0.55, 0.75, -0.1)), ("WHITE", (0.55, 0.55, 0.55))] + [("RAINBOW", rainbow(t)) for t in (1.2, 2.6, 4.4)]
def tint(img, a, b, c):
    px = img.load(); out = Image.new("RGBA", img.size); po = out.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, bl, al = px[x, y]
            f = lambda v: max(0, min(255, int(v)))
            po[x, y] = (f(a * r + b * g + c * bl), f(c * r + a * g + b * bl), f(b * r + c * g + a * bl), al)
    return out
cell = 110
sheet = Image.new("RGB", (cell * len(tiers), 22 + cell * len(sprites)), (34, 30, 44))
d = ImageDraw.Draw(sheet)
for col, (name, m) in enumerate(tiers):
    d.text((col * cell + 8, 5), name, fill=(230, 230, 230))
    for row, path in enumerate(sprites):
        im = Image.open(path).convert("RGBA")
        im.thumbnail((cell - 10, cell - 10))
        t = tint(im, *m)
        sheet.paste(t, (col * cell + (cell - t.size[0]) // 2, 22 + row * cell + (cell - t.size[1]) // 2), t)
sheet.save(out)
