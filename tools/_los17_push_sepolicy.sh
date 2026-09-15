#!/bin/bash
# A1000 / LOS 17.1: залить собранную политику SELinux на живой аппарат (adb root +
# remount), мимо system.img. Звать из Git Bash после `m selinux_policy`.
#
# Аппарат грузит precompiled_sepolicy из /vendor/etc/selinux, если её хеши
# совпали с plat- и product-частями, иначе init сам собирает CIL через secilc.
# Поэтому кладём ВСЁ содержимое трёх каталогов selinux разом — половинчатая
# заливка = рассинхрон хешей и компиляция политики при каждой загрузке.
# Метки файлов на /system из file_contexts при заливке сами не встанут:
# после перезагрузки с новой политикой — restorecon на наши бинарники.
set -e
export MSYS_NO_PATHCONV=1
A=/c/Android/sdk/platform-tools/adb.exe
# vendor и product отдельных разделов не имеют: лежат внутри system.
O=out/target/product/a1000/system
W='C:\Users\STANIS~1\AppData\Local\Temp\a1000_sepol'
rm -rf /c/Users/STANIS~1/AppData/Local/Temp/a1000_sepol
wsl.exe -d Debian -u root -e bash /mnt/c/Users/Stanislav/Desktop/NPU/firmware/_w17.sh \
  "mkdir -p /mnt/c/Users/STANIS~1/AppData/Local/Temp/a1000_sepol && cd $O && tar cf /mnt/c/Users/STANIS~1/AppData/Local/Temp/a1000_sepol/sepol.tar etc/selinux vendor/etc/selinux product/etc/selinux" | tr -d '\0'
$A remount >/dev/null
$A push "$W\\sepol.tar" /data/local/tmp/sepol.tar
$A shell 'set -e; cd /data/local/tmp; rm -rf sepol; mkdir sepol; cd sepol; tar xf ../sepol.tar
for d in etc/selinux vendor/etc/selinux product/etc/selinux; do
  cp -r $d/. /system/$d/
  echo "$d: $(ls $d | wc -l) файлов"
done
sync'
