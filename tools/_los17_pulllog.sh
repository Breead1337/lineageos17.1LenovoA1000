#!/bin/bash
# Снять журнал загрузки из СЫРОГО раздела cache (mmcblk0p19), куда пишет
# служба a1000_earlylog. Ждём появления TWRP на USB и тянем через exec-out:
# обычный `adb shell dd > файл` портит двоичные данные переводом строк.
A="/c/Users/Stanislav/Desktop/platform-tools/adb.exe"
cd /c/Users/Stanislav/Desktop/NPU/firmware || exit 1
OUT=${1:-_bootlog2.bin}
for i in $(seq 1 40); do
  MSYS_NO_PATHCONV=1 "$A" kill-server >/dev/null 2>&1
  D=$(MSYS_NO_PATHCONV=1 "$A" devices 2>&1)
  case "$D" in *recovery*|*device*) echo "аппарат на связи (заход $i)"; break;; esac
  sleep 6
done
MSYS_NO_PATHCONV=1 "$A" exec-out "dd if=/dev/block/mmcblk0p19 bs=1048576 count=4 2>/dev/null" > "$OUT"
ls -l "$OUT"
