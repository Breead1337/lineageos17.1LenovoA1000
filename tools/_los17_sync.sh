#!/bin/bash
# Докачка дерева LOS 17.1. Часть проектов тянется напрямую с android.googlesource.com,
# а он отсюда отвечает через раз (таймауты/обрыв TLS) — поэтому цикл с повторами.
M=/home/ard/los17
mountpoint -q $M || mount -o loop /mnt/d/los17.img $M
cd $M
if [ ! -d .repo ]; then
  repo init -u https://github.com/LineageOS/android.git -b lineage-17.1 --depth=1 --no-clone-bundle
fi
rm -f /home/ard/los17_sync.done
for i in $(seq 1 12); do
  echo "=== попытка $i: $(date) ==="
  if repo sync -c --no-tags --no-clone-bundle --optimized-fetch --force-sync -j4; then
    echo "SYNC_OK"
    echo ok > /home/ard/los17_sync.done
    break
  fi
  echo "--- не всё скачалось, повтор через 60 с ---"
  sleep 60
done
du -sh $M
echo done > /home/ard/los17_sync.finished
