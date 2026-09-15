#!/bin/bash
# Перезагрузить из TWRP в систему и снять logcat, пока она крутит перезапуск SF.
A="/c/Users/Stanislav/Desktop/platform-tools/adb.exe"
cd /c/Users/Stanislav/Desktop/NPU/firmware || exit 1
a() { MSYS_NO_PATHCONV=1 "$A" "$@" 2>&1; }
a reboot >/dev/null
for i in $(seq 1 18); do
  sleep 10
  MSYS_NO_PATHCONV=1 "$A" kill-server >/dev/null 2>&1
  R=$(a shell getprop ro.build.version.release | tr -d '\r\n')
  echo "  $((i*10))с: release=[$R]"
  [ "$R" = "10" ] && break
done
a logcat -d -b all > _logcat.txt
wc -l _logcat.txt
