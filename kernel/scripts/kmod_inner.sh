#!/bin/bash
cd /a1000k || exit 9
export ARCH=arm
export CROSS_COMPILE=/toolchain48/bin/arm-eabi-
export PATH=/toolchain48/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export KBUILD_BUILD_TIMESTAMP="$(date) by baton4iks"
make -j4 ARCH=arm CROSS_COMPILE=/toolchain48/bin/arm-eabi- modules 2>&1 | tail -15
echo "=== собранные модули ==="
find . -name "*.ko" -newermt "-2 hours" -printf "%p  %s\n"
