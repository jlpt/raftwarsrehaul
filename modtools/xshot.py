"""Convert an XWD dump (32bpp TrueColor ZPixmap) to PNG: xshot.py in.xwd out.png"""
import struct, sys
from PIL import Image
data = open(sys.argv[1], "rb").read()
f = struct.unpack(">25I", data[:100])
header_size, w, h, bpp, bpl, ncolors = f[0], f[4], f[5], f[11], f[12], f[19]
off = header_size + ncolors * 12
img = Image.frombuffer("RGBX", (w, h), data[off: off + bpl * h], "raw", "BGRX", bpl, 1).convert("RGB")
img.save(sys.argv[2])
print(w, h)
