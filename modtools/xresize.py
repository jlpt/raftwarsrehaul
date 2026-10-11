"""Move+resize every top-level window on $DISPLAY (there's no window manager on Xephyr to do it):
   xresize.py W H"""
import ctypes, os, sys
x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XDefaultRootWindow.restype = ctypes.c_ulong
dp = ctypes.c_void_p(x11.XOpenDisplay(os.environ["DISPLAY"].encode()))
root = ctypes.c_ulong(x11.XDefaultRootWindow(dp))
r, p = ctypes.c_ulong(), ctypes.c_ulong()
kids = ctypes.POINTER(ctypes.c_ulong)(); n = ctypes.c_uint()
x11.XQueryTree(dp, root, ctypes.byref(r), ctypes.byref(p), ctypes.byref(kids), ctypes.byref(n))
for i in range(n.value):
    x11.XMoveResizeWindow(dp, ctypes.c_ulong(kids[i]), 0, 0, int(sys.argv[1]), int(sys.argv[2]))
x11.XFlush(dp); x11.XCloseDisplay(dp)
print("resized", n.value, "windows")
