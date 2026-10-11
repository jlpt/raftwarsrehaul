#!/bin/bash
# screenshot the virtual display: vshot.sh name
DISPLAY=:99 xwd -root -silent > build/$1.xwd && python3 -I modtools/xshot.py build/$1.xwd build/$1.png >/dev/null
