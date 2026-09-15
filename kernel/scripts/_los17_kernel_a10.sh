#!/bin/bash
# Ядро под Android 10 (LOS 17.1).
#
# База — конфиг ядра #104 (тот, на котором работает девятка). Сверху добавлены
# требования AOSP из kernel/configs/q/android-4.9/android-base.config, которые
# наше 3.10 умеет; чего в 3.10 нет (BPF, USB_CONFIGFS, PM_WAKELOCKS, XFRM_INTERFACE,
# SYNC_FILE, MULTIUSER, HARDENED_USERCOPY) — пропущено осознанно, десятка на таких
# ядрах живёт со старыми путями (android_usb sysfs, xt_qtaguid вместо eBPF).
#
# ВАЖНО (как и в _los16_kernel_build.sh): в дереве ядра лежат НЕЗАКОММИЧЕННЫЕ
# правки под 4.4 — prox_enable и CONFIG_ENABLE_SIMULATIONS_PROXIMITY убивают тач
# на 9/10. Скрипт снимает их на время сборки и возвращает обратно.
set -e
K=/home/ard/a1000-kernel
SAVE=/tmp/kernel_44_save_a10
FILES44="arch/arm/mach-sc/ontim_device.c drivers/ontim/touchscreen/mstar/msg22xx/mstar_drv_self_fw_control.c arch/arm/configs/a1000_baton4iks_defconfig"

restore() {
    cd $K
    for f in $FILES44; do
        [ -f "$SAVE/$(basename $f)" ] && cp -f "$SAVE/$(basename $f)" "$f"
    done
    [ -f $SAVE/.config ] && cp -f $SAVE/.config $K/.config
    echo "=== правки 4.4 и прежний .config возвращены ==="
}
trap restore EXIT

rm -rf $SAVE && mkdir -p $SAVE
cd $K
for f in $FILES44; do cp -f "$f" "$SAVE/$(basename $f)"; done
cp -f .config $SAVE/.config
git checkout -- $FILES44
sed -i 's/^CONFIG_ENABLE_SIMULATIONS_PROXIMITY=y$/# CONFIG_ENABLE_SIMULATIONS_PROXIMITY is not set/' .config

# Требования Android 10 (quota/taskstats/xt_*/crypto). Пока ВЫКЛЮЧЕНЫ по
# умолчанию, но НЕ потому что ломают загрузку: та проверка была негодной —
# тестовые образы собирались mkbootimg БЕЗ --dt, а без дерева устройств
# загрузчик SC8830 не берёт вообще ничего. Ядро #108 с деревом загрузилось
# нормально. Вернуть A10_EXTRA=1, когда система начнёт грузиться.
if [ "${A10_EXTRA:-0}" = "1" ]; then
echo "############ добавляю требования Android 10 ############"
for c in \
  CONFIG_NETFILTER_XT_MATCH_OWNER CONFIG_NETFILTER_XT_TARGET_TCPMSS \
  CONFIG_QUOTA CONFIG_QUOTACTL CONFIG_QFMT_V2 CONFIG_QUOTA_TREE \
  CONFIG_TASKSTATS CONFIG_TASK_XACCT CONFIG_TASK_IO_ACCOUNTING CONFIG_TASK_DELAY_ACCT \
  CONFIG_IKCONFIG CONFIG_IKCONFIG_PROC CONFIG_IP_MULTICAST \
  CONFIG_CRYPTO_GCM CONFIG_CRYPTO_SHA512 CONFIG_CRYPTO_NULL ; do
  sed -i "s/^# $c is not set\$/$c=y/" .config
  grep -q "^$c=y" .config || echo "$c=y" >> .config
done
fi

# CONFIG_PROC_DEVICETREE — без него нет /proc/device-tree, а первая стадия
# init в десятке берёт fstab ТОЛЬКО оттуда (ReadFstabFromDt). Проверено на
# аппарате: каталога не было, узел в sprd.dtb добавлен, но прочитать его
# было неоткуда — init молча пропускал монтирование.
sed -i "s|^# CONFIG_PROC_DEVICETREE is not set|CONFIG_PROC_DEVICETREE=y|" .config
grep -q "^CONFIG_PROC_DEVICETREE=y" .config || echo "CONFIG_PROC_DEVICETREE=y" >> .config

# PSTORE/RAMOOPS: у ядра #89 (на нём TWRP) ramoops живёт по 0xbfbe0000, и
# консоль упавшей загрузки переживает перезагрузку. Без этих опций в ядре
# десятки /sys/fs/pstore пуст и причину падения не увидеть.
# ---- параметры загрузки, которые загрузчик A1000 выбрасывает ----
# Проверено на аппарате: /proc/cmdline от загрузчика — своя строка, нашей из
# boot.img в ней НЕТ. В десятке это фатально: первая стадия init ищет
# /fstab.${ro.hardware} строго по androidboot.hardware, отката на /proc/cpuinfo
# (как во второй стадии у 8.1/9) там нет — fstab не найден, system не
# смонтирован, загрузка мертва. Заодно теряется androidboot.selinux=permissive.
# CMDLINE_EXTEND дописывает наши параметры к строке загрузчика, не заменяя её.
# Вывод ядра глушит loglevel=1 от загрузчика: в ramoops попадали 88 байт.
# Именно printk.ignore_loglevel=1, а НЕ голый ignore_loglevel: наши параметры
# дописываются в НАЧАЛО строки (проверено на аппарате), loglevel=1 идёт следом
# и в раннем проходе перебивает уровень обратно. Параметр модуля printk
# разбирается позже и выигрывает.
sed -i "s|^CONFIG_CMDLINE=.*|CONFIG_CMDLINE=\"androidboot.hardware=sc8830 androidboot.selinux=permissive printk.ignore_loglevel=1\"|" .config
grep -q "^CONFIG_CMDLINE=" .config || echo 'CONFIG_CMDLINE="androidboot.hardware=sc8830 androidboot.selinux=permissive printk.ignore_loglevel=1"' >> .config
sed -i "s|^CONFIG_CMDLINE_FROM_BOOTLOADER=y|# CONFIG_CMDLINE_FROM_BOOTLOADER is not set|" .config
sed -i "s|^# CONFIG_CMDLINE_EXTEND is not set|CONFIG_CMDLINE_EXTEND=y|" .config
grep -q "^CONFIG_CMDLINE_EXTEND=y" .config || echo "CONFIG_CMDLINE_EXTEND=y" >> .config

yes "" | make ARCH=arm oldconfig >/dev/null 2>&1 || true

echo "############ что реально включилось ############"
for c in CONFIG_NETFILTER_XT_MATCH_OWNER CONFIG_NETFILTER_XT_TARGET_TCPMSS CONFIG_QUOTA \
         CONFIG_QUOTACTL CONFIG_QFMT_V2 CONFIG_TASKSTATS CONFIG_TASK_IO_ACCOUNTING \
         CONFIG_IKCONFIG_PROC CONFIG_IP_MULTICAST CONFIG_CRYPTO_GCM CONFIG_CPUSETS \n         CONFIG_CMDLINE_EXTEND CONFIG_CMDLINE; do
  printf "  %-38s %s\n" "$c" "$(grep -E "^($c=|# $c )" .config || echo НЕТ)"
done
cp -f .config /home/ard/a1000-kernel/.config.a10

echo "############ сборка ядра и модулей ############"
# Модули (mali/sprdwl/trout_fm) ОБЯЗАТЕЛЬНО пересобирать вместе с ядром: правка
# конфига сменила module_layout (0xb9384d63 -> другой), и старые .ko не встанут —
# это GPU, Wi-Fi и FM.
cat > $K/kbuild_a10_inner.sh <<'INNER'
#!/bin/bash
cd /a1000k || exit 9
export ARCH=arm CROSS_COMPILE=/toolchain48/bin/arm-eabi-
export PATH=/toolchain48/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export KBUILD_BUILD_TIMESTAMP="$(date) by baton4iks"
make -j4 ARCH=arm Image 2>&1 | tail -6
make -j4 ARCH=arm modules 2>&1 | tail -6
ls -la arch/arm/boot/Image
echo "=== module_layout ==="
grep -w module_layout Module.symvers
echo "=== строка версии ==="
strings -a arch/arm/boot/Image | grep -m1 "Linux version"
INNER
chmod +x $K/kbuild_a10_inner.sh
mkdir -p /home/ard/bionic/a1000k /home/ard/bionic/toolchain48
mountpoint -q /home/ard/bionic/a1000k || mount --bind $K /home/ard/bionic/a1000k
mountpoint -q /home/ard/bionic/toolchain48 || mount --bind /home/ard/arm-eabi-4.8-toolchain-master /home/ard/bionic/toolchain48
mountpoint -q /home/ard/bionic/proc || mount -t proc proc /home/ard/bionic/proc
mountpoint -q /home/ard/bionic/dev  || mount --rbind /dev /home/ard/bionic/dev
chroot /home/ard/bionic /bin/bash /a1000k/kbuild_a10_inner.sh

echo "############ раскладываю в дерево 17.1 ############"
T=/home/ard/los17
F=/mnt/c/Users/Stanislav/Desktop/NPU/firmware
# Образ дерева может быть не примонтирован (WSL его отпускает при простое).
# Без этого проверки "[ -d ... ]" ниже молча пропускали копирование, и в
# boot.img уезжало СТАРОЕ ядро — на это уже потеряли два круга отладки.
mountpoint -q $T || mount -o loop /mnt/d/los17.img $T
cp -f $K/arch/arm/boot/Image $F/Image_a10
[ -d $T/device/lenovo/a1000/prebuilt ] && cp -f $K/arch/arm/boot/Image $T/device/lenovo/a1000/prebuilt/kernel
M=$T/vendor/lenovo/a1000/proprietary/lib/modules
if [ -d $M ]; then
  cp -f $K/drivers/gpu/mali400/r4p1/mali.ko      $M/mali.ko
  cp -f $K/drivers/net/wireless/sprdwl/sprdwl.ko $M/sprdwl.ko
  cp -f $K/drivers/misc/fm_2351/trout_fm.ko      $M/trout_fm.ko
  ls -la $M/*.ko
fi
ls -la $F/Image_a10
