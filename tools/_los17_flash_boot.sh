#!/bin/bash
# Прошить системный boot (#113) в mmcblk0p16 — там сейчас лежит TWRP,
# поэтому аппарат всегда грузится в recovery. TWRP остаётся на p20.
# Ждёт появления adb (аппарат в TWRP), потом пишет и сверяет.
A="/c/Users/Stanislav/Desktop/platform-tools/adb.exe"
cd /c/Users/Stanislav/Desktop/NPU/firmware || exit 1
IMG=_los17_boot.img
run(){ MSYS_NO_PATHCONV=1 "$A" "$@"; }

echo "жду аппарат в TWRP (adb)..."
for i in $(seq 1 120); do
  [ -n "$(run shell 'echo up' 2>/dev/null | tr -d '\r\n')" ] && break
  sleep 5
done
[ -n "$(run shell 'echo up' 2>/dev/null | tr -d '\r\n')" ] || { echo "аппарат не появился"; exit 1; }

# карта разделов сдвигается — сверяем by-name, а не память
BOOT=$(run shell 'readlink -f /dev/block/platform/*/by-name/boot' | tr -d '\r\n')
echo "boot = $BOOT"
case "$BOOT" in /dev/block/mmcblk0p*) ;; *) echo "by-name/boot не найден"; exit 1;; esac

run push "$IMG" /tmp/b.img || exit 1
run shell "dd if=/tmp/b.img of=$BOOT bs=1048576 conv=notrunc; sync"
# сверка ровно по длине образа (раздел больше)
BLK=$(( $(stat -c %s "$IMG") / 512 ))
echo "на аппарате: $(run shell "dd if=$BOOT bs=512 count=$BLK 2>/dev/null | md5sum" | tr -d '')"
echo "локально:    $(md5sum "$IMG")"
echo "хеши сошлись -> adb reboot"
