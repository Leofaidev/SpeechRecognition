#!/bin/bash
XAUTH=$(ls /run/user/1001/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
export DISPLAY=:0
export XAUTHORITY=$XAUTH
# Move mouse to content area center
xdotool mousemove 400 220
sleep 0.3
# Scroll down 5 times (Button-5)
for i in 1 2 3 4 5; do
  xdotool click 5
  sleep 0.1
done
