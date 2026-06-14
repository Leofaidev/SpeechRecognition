#!/bin/bash
pkill -f 'python.*gui.app' 2>/dev/null
sleep 1
XAUTH=$(ls /run/user/1001/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
export DISPLAY=:0
export XAUTHORITY=$XAUTH
screen -dmS wsp bash -c 'cd /home/claude/SpeechRecognition/src && /home/claude/SpeechRecognition/.venv-linux/bin/python -m gui.app'
