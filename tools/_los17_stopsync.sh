#!/bin/bash
pkill -f "_los17_sync.sh"
pkill -f "repo -- sync"
pkill -f "main.py --repo-dir=/home/ard/los17"
sleep 3
pgrep -af "_los17_sync|repo -- sync" | grep -v pkill | head -3 || echo "синк остановлен"
