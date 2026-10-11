"""Send synthetic input to an X display via XTest.
   xinput.py click X Y | hold X Y MS | key NAME [ms] | move X Y | focus   (uses $DISPLAY)"""
import ctypes, os, sys, time
x11 = ctypes.cdll.LoadLibrary("libX11.so.6"); xt = ctypes.cdll.LoadLibrary("libXtst.so.6")
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XDefaultRootWindow.restype = ctypes.c_ulong
x11.XStringToKeysym.restype = ctypes.c_ulong
d = x11.XOpenDisplay(os.environ["DISPLAY"].encode())
dp = ctypes.c_void_p(d)
cmd = sys.argv[1]
if cmd in ("click", "move", "hold"):
    xt.XTestFakeMotionEvent(dp, -1, int(sys.argv[2]), int(sys.argv[3]), 0); x11.XFlush(dp); time.sleep(0.15)
    if cmd == "click":
        xt.XTestFakeButtonEvent(dp, 1, 1, 0); x11.XFlush(dp); time.sleep(0.08)
        xt.XTestFakeButtonEvent(dp, 1, 0, 0); x11.XFlush(dp)
    elif cmd == "hold":  # hold mouse button 1 for MS milliseconds (fire)
        xt.XTestFakeButtonEvent(dp, 1, 1, 0); x11.XFlush(dp); time.sleep(int(sys.argv[4]) / 1000)
        xt.XTestFakeButtonEvent(dp, 1, 0, 0); x11.XFlush(dp)
elif cmd == "focus":
    root = x11.XDefaultRootWindow(dp)
    rr, child = ctypes.c_ulong(), ctypes.c_ulong()
    a = ctypes.c_int(); m = ctypes.c_uint()
    x11.XQueryPointer(dp, ctypes.c_ulong(root), ctypes.byref(rr), ctypes.byref(child), ctypes.byref(a), ctypes.byref(a), ctypes.byref(a), ctypes.byref(a), ctypes.byref(m))
    x11.XSetInputFocus(dp, child, 2, 0); x11.XFlush(dp)
    print("focused window", hex(child.value))
elif cmd == "key":
    code = x11.XKeysymToKeycode(dp, x11.XStringToKeysym(sys.argv[2].encode()))
    hold = int(sys.argv[3]) / 1000 if len(sys.argv) > 3 else 0.08
    xt.XTestFakeKeyEvent(dp, code, 1, 0); x11.XFlush(dp); time.sleep(hold)
    xt.XTestFakeKeyEvent(dp, code, 0, 0); x11.XFlush(dp)
x11.XCloseDisplay(dp)
