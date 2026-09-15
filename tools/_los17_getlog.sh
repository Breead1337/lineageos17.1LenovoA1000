#!/bin/bash
# Снять лог упавшей загрузки: залить отладочный boot (ядро десятки + userspace
# TWRP + дерево устройств) из фастбута, дождаться adb и вытащить ramoops.
A="/c/Users/Stanislav/Desktop/platform-tools/adb.exe"
FB="/c/Users/Stanislav/Desktop/platform-tools/fastboot.exe"
cd /c/Users/Stanislav/Desktop/NPU/firmware
MSYS_NO_PATHCONV=1 "$FB" flash boot '_boot_dbg.img' >/dev/null 2>&1
MSYS_NO_PATHCONV=1 "$FB" reboot >/dev/null 2>&1
for i in $(seq 1 15); do
  sleep 12
  MSYS_NO_PATHCONV=1 "$A" kill-server >/dev/null 2>&1
  [ -n "$(MSYS_NO_PATHCONV=1 "$A" shell 'echo up' 2>/dev/null | tr -d '\r\n')" ] && break
done
MSYS_NO_PATHCONV=1 "$A" pull /sys/fs/pstore/console-ramoops-0 _crashlog.txt >/dev/null 2>&1
wc -c _crashlog.txt
