#!/bin/bash
# Один круг отладки загрузки Android 10 без участия человека.
#
# 1. из любого TWRP уходим в фастбут и грузим отладочный boot
#    (ядро десятки + userspace TWRP + дерево устройств) — в нём есть pstore;
# 2. СТИРАЕМ запись ramoops (удаление файла в pstore чистит зону, иначе на
#    следующем круге читаем прошлый лог и гоняемся за призраком — наступали);
# 3. заливаем настоящий boot.img десятки и перезагружаемся;
# 4. ждём исхода: загрузилось / фастбут / упало в recovery;
# 5. возвращаемся в отладочный boot и забираем свежий лог в _crashlog.txt.
A="/c/Users/Stanislav/Desktop/platform-tools/adb.exe"
FB="/c/Users/Stanislav/Desktop/platform-tools/fastboot.exe"
cd /c/Users/Stanislav/Desktop/NPU/firmware || exit 1

adb_() { MSYS_NO_PATHCONV=1 "$A" "$@" 2>/dev/null; }
fb_()  { MSYS_NO_PATHCONV=1 "$FB" "$@" 2>&1; }

wait_adb() {  # $1 — сколько секунд ждать
  for i in $(seq 1 $(( ${1:-180} / 10 ))); do
    sleep 10
    MSYS_NO_PATHCONV=1 "$A" kill-server >/dev/null 2>&1
    [ -n "$(adb_ shell 'echo up' | tr -d '\r\n')" ] && return 0
  done
  return 1
}

to_fastboot() {
  if [ "$(fb_ devices | grep -c fastboot)" -gt 0 ]; then return 0; fi
  adb_ reboot bootloader
  for i in $(seq 1 20); do
    sleep 5
    [ "$(fb_ devices | grep -c fastboot)" -gt 0 ] && return 0
  done
  return 1
}

boot_dbg() {
  to_fastboot || { echo "не смог попасть в фастбут"; return 1; }
  fb_ flash boot _boot_dbg.img >/dev/null
  fb_ reboot >/dev/null
  wait_adb 180 || { echo "отладочный boot не поднялся"; return 1; }
}

echo "--- гружу отладочный boot ---"
boot_dbg || exit 1
echo "--- чищу ramoops ---"
adb_ shell "rm -f /sys/fs/pstore/console-ramoops-0" >/dev/null
echo "--- заливаю boot.img десятки ---"
adb_ push _los17_boot.img /tmp/b.img >/dev/null
adb_ shell "dd if=/tmp/b.img of=/dev/block/mmcblk0p16 bs=1048576 conv=notrunc; sync; rm -f /tmp/b.img"
adb_ reboot
echo "--- жду исхода ---"
for i in $(seq 1 20); do
  sleep 15
  MSYS_NO_PATHCONV=1 "$A" kill-server >/dev/null 2>&1
  B=$(adb_ shell getprop sys.boot_completed | tr -d '\r\n')
  R=$(adb_ shell getprop ro.build.version.release | tr -d '\r\n')
  F=$(fb_ devices | grep -c fastboot)
  echo "  $((i*15))с: release=[$R] boot=[$B] fastboot=$F"
  [ "$B" = "1" ] && { echo "=== ЗАГРУЗИЛСЯ ==="; exit 0; }
  [ "$F" -gt 0 ] && { echo "  ушёл в фастбут"; break; }
  [ "$R" = "5.1.1" ] && { echo "  ушёл в recovery"; break; }
done
echo "--- снимаю лог ---"
boot_dbg || exit 1
adb_ pull /sys/fs/pstore/console-ramoops-0 _crashlog.txt >/dev/null
wc -c _crashlog.txt
