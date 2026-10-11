"""Poll the :99 display until a region matches a reference screenshot.
   wait_for.py ref.png x0 y0 x1 y1 timeout_s [click_x click_y]"""
import os, subprocess, sys, time
from PIL import Image, ImageChops, ImageStat
ref, box, timeout = sys.argv[1], tuple(map(int, sys.argv[2:6])), float(sys.argv[6])
click = sys.argv[7:9]
here = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, DISPLAY=":99")
refimg = Image.open(ref).convert("RGB").crop(box)
t0 = time.time(); n = 0
while time.time() - t0 < timeout:
    raw = subprocess.run(["xwd", "-root", "-silent"], env=env, capture_output=True).stdout
    open("/tmp/claude-1000/_w.xwd", "wb").write(raw)
    subprocess.run([sys.executable, "-I", f"{here}/xshot.py", "/tmp/claude-1000/_w.xwd", "/tmp/claude-1000/_w.png"], capture_output=True)
    cur = Image.open("/tmp/claude-1000/_w.png").convert("RGB").crop(box)
    diff = sum(ImageStat.Stat(ImageChops.difference(cur, refimg)).mean) / 3
    if diff < 5:
        print(f"matched after {time.time() - t0:.0f}s (diff {diff:.1f})"); sys.exit(0)
    n += 1
    if click and n % 3 == 0:
        subprocess.run([sys.executable, "-I", f"{here}/xinput.py", "click", *click], env=env)
    time.sleep(2)
print("timeout"); sys.exit(1)
