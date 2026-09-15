#!/bin/bash
# Докачать настоящий webview.apk: в дереве лежит указатель git-lfs на 133 байта,
# из-за чего aapt2 падает «failed opening zip: Invalid file».
# Сеть до github рвётся, поэтому с повторами. Лог: /home/ard/los17_webview.log
T=/home/ard/los17/external/chromium-webview/prebuilt/arm
L=/home/ard/los17_webview.log
: > $L
rm -f /home/ard/los17_webview.finished
mountpoint -q /home/ard/los17 || mount -o loop /mnt/d/los17.img /home/ard/los17
cd $T || exit 1
for i in $(seq 1 12); do
  echo "=== попытка $i: $(date) ===" >> $L
  git lfs pull >> $L 2>&1
  SZ=$(stat -c%s webview.apk)
  echo "размер: $SZ" >> $L
  if [ "$SZ" -gt 1000000 ]; then
    echo "СКАЧАН" >> $L
    break
  fi
  sleep 20
done
echo done > /home/ard/los17_webview.finished
