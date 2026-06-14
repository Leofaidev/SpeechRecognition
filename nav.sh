#!/bin/bash
XAUTH=$(ls /run/user/1001/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
export DISPLAY=:0
export XAUTHORITY=$XAUTH
xdotool mousemove $1 $2 click 1
sleep ${3:-0.6}
