#!/bin/bash
# Пробная примерка правок 8.1 на дерево 17.1 (ничего не меняем, только проверка).
P=/home/ard/a1000_81_patches
T=/home/ard/los17
declare -A MAP=(
 [bootable_recovery]=bootable/recovery
 [external_noto-fonts]=external/noto-fonts
 [external_tinyalsa]=external/tinyalsa
 [external_wpa_supplicant_8]=external/wpa_supplicant_8
 [frameworks_base]=frameworks/base
 [frameworks_native]=frameworks/native
 [hardware_interfaces]=hardware/interfaces
 [hardware_ril]=hardware/ril
 [lineage-sdk]=lineage-sdk
 [packages_apps_FMRadio]=packages/apps/FMRadio
 [packages_apps_PackageInstaller]=packages/apps/PackageInstaller
 [packages_apps_Recorder]=packages/apps/Recorder
 [packages_apps_Settings]=packages/apps/Settings
 [packages_inputmethods_LatinIME]=packages/inputmethods/LatinIME
 [system_bt]=system/bt
 [system_connectivity_wificond]=system/connectivity/wificond
 [system_core]=system/core
 [system_sepolicy]=system/sepolicy
)
for k in "${!MAP[@]}"; do
  d=${MAP[$k]}; f=$P/$k.patch
  [ -f "$f" ] || continue
  if [ ! -d "$T/$d" ]; then printf "%-34s НЕТ КАТАЛОГА\n" "$d"; continue; fi
  cd $T/$d
  tot=$(grep -c "^diff --git" $f)
  if git apply --check "$f" 2>/dev/null; then
    printf "%-34s ЛОЖИТСЯ ЦЕЛИКОМ (%s файлов)\n" "$d" "$tot"
  else
    ok=$(git apply --numstat "$f" 2>/dev/null | wc -l)
    bad=$(git apply --check "$f" 2>&1 | grep -c "^error")
    printf "%-34s НЕ ЛОЖИТСЯ: %s ошибок из %s файлов\n" "$d" "$bad" "$tot"
  fi
done
