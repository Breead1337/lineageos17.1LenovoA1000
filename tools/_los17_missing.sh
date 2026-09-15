#!/bin/bash
for d in libcore system/tools/hidl system/nfc external/curl external/pcre external/jsilver \
         external/seccomp-tests external/autotest packages/apps/CertInstaller packages/apps/AudioFX \
         hardware/intel/common/bd_prov; do
  printf "%-34s %s файлов\n" "$d" "$(ls -A /home/ard/los17/$d 2>/dev/null | wc -l)"
done
pgrep -f _los17_sync.sh >/dev/null && echo "СИНК ИДЁТ" || echo "СИНК СТОИТ"
