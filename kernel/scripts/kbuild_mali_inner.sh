#!/bin/bash
cd /a1000k || exit 9
export ARCH=arm CROSS_COMPILE=/toolchain48/bin/arm-eabi-
export PATH=/toolchain48/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
make -j4 ARCH=arm CROSS_COMPILE=/toolchain48/bin/arm-eabi- M=drivers/gpu/mali400/r4p1 modules 2>&1 | tail -6
ls -la drivers/gpu/mali400/r4p1/mali.ko
