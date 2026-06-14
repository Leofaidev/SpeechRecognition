#!/bin/bash
XAUTH=$(ls /run/user/1001/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
export DISPLAY=:0
export XAUTHORITY=$XAUTH
xdotool mousemove 464 330 click 1
sleep 0.8
xdotool mousemove 464 376 click 1
sleep 0.8
