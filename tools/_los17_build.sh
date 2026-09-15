#!/bin/bash
# Полная сборка LOS 17.1 для a1000. Лог: /home/ard/los17_build.log
rm -f /home/ard/los17_build.finished
: > /home/ard/los17_build.log
bash /mnt/c/Users/Stanislav/Desktop/NPU/firmware/_los17.sh "${1:-mka bacon -j6}" >> /home/ard/los17_build.log 2>&1
echo "RC=$?" >> /home/ard/los17_build.log
echo done > /home/ard/los17_build.finished
