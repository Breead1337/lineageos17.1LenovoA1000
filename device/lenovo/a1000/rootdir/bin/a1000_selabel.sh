#!/system/bin/sh
# A1000: расставить SELinux-метки вендорным узлам.
#
# ЗАЧЕМ. В enforcing почти всё, обо что спотыкалась система, — проблема МЕТОК,
# а не отсутствующих правил: узлы остались с общими типами (device, sysfs),
# которых базовой политике никто не разрешал. Нужные типы (gpu_device,
# sysfs_batteryinfo, sysfs_leds, sysfs_devices_system_cpu, radio_device) в
# политике уже есть и уже разрешены нужным доменам.
#
# Немногое, что метками не лечится, дописано ПРЯМО В ДВОИЧНУЮ ПОЛИТИКУ
# инструментом a1000_sepolicy_inject (см. firmware/_sepolicy_rules.txt):
# пересобирать дерево не пришлось, рабочий ramdisk собран другим деревом.
#
# ПОЧЕМУ find, А НЕ ЦИКЛ ПО "$dir"/*
# Первая версия ходила по маске и звала chcon на всё подряд. В sysfs среди
# файлов лежат симлинки (device, subsystem), chcon идёт ПО ССЫЛКЕ — и каталог
# /sys/devices/sdio_emmc уехал в sysfs_leds. Вторая версия обернула это в
# функцию с проверками -f и -L, и переклейка перестала срабатывать вовсе:
# батарея осталась с типом sysfs, healthd не смог её читать и показывал 0 %.
# find -type f не ходит по ссылкам сам и не зависит от тонкостей оболочки.
#
# ПОЧЕМУ xargs, А НЕ "while read f; do chcon ... $f; done"
# Узлов около 250, и на каждый заводился отдельный процесс chcon — скрипт
# работал 22 СЕКУНДЫ. Всё это время система оставалась permissive, и Trust,
# который проверяет SELinux при старте своей службы в system_server, успевал
# увидеть permissive и повесить предупреждение «SELinux выключен». xargs
# передаёт chcon сразу пачку имён: те же метки встают меньше чем за секунду.

set -x

# A1000/Android 10: узлы /dev (mali0, sprd_gsp, misc, трубы WCN, камера,
# модем) метит ueventd по vendor/file_contexts в момент создания — это
# надёжнее: HAL не успевают ткнуться в узел со старым типом. Прежние
# chcon отсюда убраны (и /dev/mmcblk0p20 на десятке — это recovery).

# ВНИМАНИЕ: -path в здешнем toybox не работает (даёт 0 файлов), поэтому
# обходим каталоги классов. Слэш в конце важен: он заставляет find пойти ЧЕРЕЗ
# симлинк класса в реальный каталог, а -maxdepth 1 -type f не даёт зацепить
# вложенные ссылки device/subsystem.

# Батарея: healthd читает capacity/status/present/voltage_now/current_now.
find /sys/class/power_supply/*/ -maxdepth 1 -type f 2>/dev/null |
    xargs -r chcon u:object_r:sysfs_batteryinfo:s0 2>/dev/null

# Подсветка и светодиоды: hal_light.
find /sys/class/backlight/*/ /sys/class/leds/*/ -maxdepth 1 -type f 2>/dev/null |
    xargs -r chcon u:object_r:sysfs_leds:s0 2>/dev/null

# Частоты: hal_power пишет scaling_min_freq.
# КАТАЛОГИ ТОЖЕ, а не только файлы: /sys/devices/system/cpu/online читает всякий,
# кто зовёт sysconf(_SC_NPROCESSORS_ONLN) — bionic лезет туда каждый раз, а
# zygote ещё и перечисляет сам каталог. С типом sysfs это отказ у полутора
# десятков доменов (zygote, adbd, logd, netd, mediacodec, idmap, sgdisk,
# fsck_untrusted...), с типом sysfs_devices_system_cpu — ни одного, потому что
# в базовой политике есть r_dir_file(domain, sysfs_devices_system_cpu).
# -type l НЕ трогаем: chcon идёт по ссылке, так когда-то уехал sdio_emmc.
find /sys/devices/system/cpu \( -type f -o -type d \) 2>/dev/null |
    xargs -r chcon u:object_r:sysfs_devices_system_cpu:s0 2>/dev/null

# Вибромотор. Узел общего типа sysfs, а hal_vibrator_default писать туда не
# разрешено — из-за этого пропал виброотклик. Тип sysfs_vibrator в политике
# уже есть и уже разрешён этому домену.
# readlink здесь НЕ используем: он читает корень rootfs, а домену toolbox это
# не разрешено — в журнале появлялся лишний отказ. Слэш в конце пути и так
# ведёт find ЧЕРЕЗ симлинк класса, как в соседних местах выше.
find /sys/class/timed_output/*/ -maxdepth 1 -type f 2>/dev/null |
    xargs -r chcon u:object_r:sysfs_vibrator:s0 2>/dev/null

# Спящий режим.
chcon u:object_r:sysfs_power:s0 /sys/power/state 2>/dev/null

# /cache/recovery. TWRP оставляет там файлы (log, .version, recovery.fstab) с
# типом, которого в ЭТОЙ политике нет, — ядро видит unlabeled, и system_server
# не может их удалить. А через этот каталог идут СБРОС ДО ЗАВОДСКИХ и OTA.
find /cache/recovery -maxdepth 1 -type f 2>/dev/null |
    xargs -r chcon u:object_r:cache_recovery_file:s0 2>/dev/null

# Наш шим. Метку system_lib_file ставить НЕЛЬЗЯ: такого типа в здешней
# политике нет, ядро видит файл как unlabeled и запрещает его исполнять —
# из-за этого не поднималась камера. Соседние библиотеки имеют system_file.
# Клеим ТОЛЬКО если метка отличается: на /system метки хранятся в самой
# файловой системе и переживают перезагрузку, а лишний chcon упирается в
# запрет relabelfrom и сорит в журнале.
case "$(ls -Z /system/lib/libui_shim.so 2>/dev/null)" in
    *system_file*) ;;
    *) chcon u:object_r:system_file:s0 /system/lib/libui_shim.so 2>/dev/null ;;
esac

# Переход в enforcing — только по свойству, по умолчанию выключено:
#   setprop persist.a1000.selinux 1   (и перезагрузка)
# Метки ставятся ВЫШЕ, до этой строки: chcon под enforcing упрётся в запрет
# relabelfrom для типов, которых нет в списке правил.
#
# СТРАХОВКА ОТ БУТ-ЛУПА. Метка ставится перед setenforce и снимается вторым
# проходом скрипта по sys.boot_completed. Значит, если загрузка с enforcing НЕ
# дошла до конца, на следующей метка ещё на месте — и мы просто не включаем
# enforcing, телефон грузится permissive. Лазить в TWRP из-за неудачного
# правила больше не нужно; чтобы попробовать снова, достаточно перезагрузиться.
FLAG=/data/local/tmp/.a1000_enforcing_try

if [ "$(getprop sys.boot_completed)" = "1" ]; then
    rm -f "$FLAG"
elif [ "$(getprop persist.a1000.selinux)" = "1" ]; then
    if [ -f "$FLAG" ]; then
        rm -f "$FLAG"
    else
        : > "$FLAG"
        setenforce 1
        log -t a1000_selinux "enforcing: $(getenforce)"
    fi
fi
