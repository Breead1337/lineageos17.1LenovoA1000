#!/bin/bash
pkill -f "_los17_build.sh"
pkill -f "_run17.sh"
pkill -f "soong_ui"
pkill -f "soong_build"
pkill -f "ninja"
pkill -f "kati"
sleep 3
echo "=== что осталось ==="
pgrep -af "soong|ninja|kati|_los17_build|_run17" | head -5
echo "=== хвост лога ==="
tail -5 /home/ard/los17_build.log 2>/dev/null
