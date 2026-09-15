#!/bin/bash
cd /a1000k || exit 9
export ARCH=arm CROSS_COMPILE=/toolchain48/bin/arm-eabi-
export PATH=/toolchain48/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export KBUILD_BUILD_TIMESTAMP="$(date) by baton4iks"
make -j4 ARCH=arm Image 2>&1 | tail -6
make -j4 ARCH=arm modules 2>&1 | tail -6
ls -la arch/arm/boot/Image
echo "=== module_layout ==="
grep -w module_layout Module.symvers
echo "=== строка версии ==="
strings -a arch/arm/boot/Image | grep -m1 "Linux version"
