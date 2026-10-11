#!/bin/bash
# screenshot the virtual display: vshot.sh name  ->  build/name.png
cd "$(dirname "$0")/.."
if command -v xwd > /dev/null; then
    DISPLAY=:99 xwd -root -silent > build/$1.xwd && python3 -I modtools/xshot.py build/$1.xwd build/$1.png > /dev/null && rm build/$1.xwd
else
    DISPLAY=:99 import -window root build/$1.png
fi
