#!/bin/bash
echo "=== git-процессы ==="
pgrep -af "git fetch|git-remote|repo" | head -5
echo "=== трафик loopback0/eth1 за 15 c ==="
a=$(cat /sys/class/net/loopback0/statistics/rx_bytes 2>/dev/null)
b=$(cat /sys/class/net/eth1/statistics/rx_bytes 2>/dev/null)
sleep 15
a2=$(cat /sys/class/net/loopback0/statistics/rx_bytes 2>/dev/null)
b2=$(cat /sys/class/net/eth1/statistics/rx_bytes 2>/dev/null)
echo "loopback0: $(( (a2-a)/1024 )) КБ, eth1: $(( (b2-b)/1024 )) КБ"
echo "=== проверка доступа к android.googlesource.com ==="
timeout 40 git ls-remote https://android.googlesource.com/platform/system/tools/hidl refs/tags/android-10.0.0_r41 2>&1 | head -3
