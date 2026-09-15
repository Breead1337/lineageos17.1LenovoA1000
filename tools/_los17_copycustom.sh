#!/bin/bash
S=/home/ard/los15.1; T=/home/ard/los17
echo "=== что внутри спорных ==="
for d in hardware/marvell prebuilts/libs autoload/dist; do
  echo "--- $d ($(du -sh $S/$d 2>/dev/null | cut -f1))"; ls $S/$d | head -5
done
echo
echo "=== копирую наши проекты ==="
for d in external/libui_shim external/libsprdsensors_shim vendor/lineage-priv hardware/marvell; do
  mkdir -p $T/$(dirname $d)
  rsync -a --exclude "*.pre-*" --exclude "*.bak*" --exclude ".git" $S/$d/ $T/$d/
  echo "  $d -> $(du -sh $T/$d | cut -f1)"
done
