#!/bin/bash
XAUTH=$(ls /run/user/1001/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
export DISPLAY=:0
export XAUTHORITY=$XAUTH
xdotool mousemove 150 286 click 1
sleep 1.0
xdotool mousemove 340 162 click 1
sleep 1.2
