#!/bin/bash
XAUTH=$(ls /run/user/1001/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
export DISPLAY=:0; export XAUTHORITY=$XAUTH
xdotool mousemove 518 322 click 1
