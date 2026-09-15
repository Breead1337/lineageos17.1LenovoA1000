#!/bin/bash
T=/home/ard/los17
for d in packages/services/Telephony packages/apps/Jelly hardware/qcom/audio hardware/qcom/keymaster \
         system/tools/hidl libcore frameworks/base frameworks/native system/core build/soong external/curl; do
  n=$(ls -A $T/$d 2>/dev/null | wc -l)
  g=$( [ -e "$T/$d/.git" ] && echo git || echo "-" )
  printf "%-34s %5s файлов  %s\n" "$d" "$n" "$g"
done
