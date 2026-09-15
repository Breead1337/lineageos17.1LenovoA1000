#!/bin/bash
# Подготовка к порту на 17.1, пока качается дерево:
#  1) свежий срез правок 8.1 (в т.ч. сегодняшняя правка keyguard);
#  2) распаковка июньского снимка дерева устройства из LOS 16 (сам tree удалён).
set -e
S=/home/ard/los15.1
O=/home/ard/a1000_81_patches
mkdir -p $O
cd $S
echo "############ правки 8.1 -> $O ############"
for p in bootable/recovery external/chromium-webview/patches external/noto-fonts \
         external/tinyalsa external/wpa_supplicant_8 frameworks/base frameworks/native \
         hardware/interfaces hardware/ril lineage-sdk packages/apps/FMRadio \
         packages/apps/PackageInstaller packages/apps/Recorder packages/apps/Settings \
         packages/inputmethods/LatinIME system/bt system/connectivity/wificond \
         system/core system/sepolicy system/netd build/make vendor/lineage; do
  n=$(echo $p | tr / _)
  if [ -e "$S/$p/.git" ]; then
    (cd $S/$p && git diff -- . ":(exclude)*.pre-*" ":(exclude)*.bak-*" > $O/$n.patch 2>/dev/null)
    L=$(wc -l < $O/$n.patch)
    [ "$L" = "0" ] && rm -f $O/$n.patch || printf "%-44s %s строк\n" "$n.patch" "$L"
  fi
done
echo
echo "############ снимок дерева устройства из LOS 16 ############"
mkdir -p /home/ard/los16_snap
tar xzf /mnt/d/a1000-backup/los16-ours-.tar.gz -C /home/ard/los16_snap
du -sh /home/ard/los16_snap/*
echo
echo "############ дерево устройства 8.1 ############"
du -sh $S/device/lenovo/a1000 $S/vendor/lenovo/a1000 2>/dev/null
