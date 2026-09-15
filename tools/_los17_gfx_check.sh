#!/bin/bash
T=/home/ard/los17
echo "=== есть ли в 17.1 ==="
for p in frameworks/native/libs/hwc2on1adapter \
         hardware/interfaces/graphics/allocator/2.0/default \
         hardware/interfaces/graphics/mapper/2.0/default \
         hardware/interfaces/graphics/composer/2.1/default; do
  [ -d $T/$p ] && echo "ЕСТЬ  $p ($(ls $T/$p | wc -l) файлов)" || echo "НЕТ   $p"
done
echo
echo "=== чем композер 2.1 собирается в 17.1 ==="
ls $T/hardware/interfaces/graphics/composer/2.1/ 2>/dev/null
grep -rn "hwc2on1\|HWC2On1" $T/hardware/interfaces/graphics/composer/2.1/ $T/frameworks/native 2>/dev/null | head -10
