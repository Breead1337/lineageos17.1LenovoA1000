# -*- coding: utf-8 -*-
u"""A1000 / LOS 17.1: SELinux enforcing.

Политика — в firmware/a1000_sepolicy_q/{public,private,vendor}, сведена из
полной загрузки в permissive. Здесь только разложить её по дереву и поправить
окружение:

* BoardConfig: SELINUX_IGNORE_NEVERALLOWS (только userdebug) — половина прав
  нашим HAL базовой политикой запрещена ради Treble, которого у A1000 нет;
* a1000_selabel.sh — в домен su: init десятки под enforcing не запускает
  службу без домена, а второй проход скрипта (по sys.boot_completed) снимает
  страховочный флаг — без него следующая загрузка молча осталась бы permissive;
* из скрипта убраны метки /dev — их теперь ставит ueventd по file_contexts
  (а /dev/mmcblk0p20 там был вообще recovery, misc на десятке = p21);
* /data/cg — restorecon под новый тип a1000_gps_data_file;
* persist.a1000.selinux=1.
"""
import io, os, shutil

T = '/home/ard/los17/device/lenovo/a1000/'
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a1000_sepolicy_q')


def rw(path, fn):
    p = T + path
    s = io.open(p, encoding='utf-8').read()
    n = fn(s)
    if n != s:
        io.open(p, 'w', encoding='utf-8', newline='\n').write(n)
        print(path + u': правлен')
    else:
        print(path + u': без изменений')


def sub(old, new, mark):
    def f(s):
        if mark in s:
            return s
        assert s.count(old) == 1, old[:60]
        return s.replace(old, new)
    return f


shutil.rmtree(T + 'sepolicy')
shutil.copytree(SRC, T + 'sepolicy')
print(u'sepolicy: скопирована из firmware/a1000_sepolicy_q')

rw('BoardConfig.mk', sub(
    'BOARD_SEPOLICY_DIRS             += device/lenovo/a1000/sepolicy/vendor\n',
    'BOARD_SEPOLICY_DIRS             += device/lenovo/a1000/sepolicy/vendor\n'
    '# Treble у A1000 нет, а базовая политика запрещает вендорным HAL то, без\n'
    '# чего наши блобы не живут (debugfs, system_data_file, сокет modemd).\n'
    '# Только для userdebug — в user-сборке система сборки откажет сама.\n'
    'SELINUX_IGNORE_NEVERALLOWS := true\n',
    'SELINUX_IGNORE_NEVERALLOWS'))

rw('device.mk', sub(
    '    # A1000/Android 10: 0, пока не портирована политика SELinux.\n'
    '    # С единицей a1000_selabel.sh делает setenforce 1 и загрузка умирает,\n'
    '    # см. _los17_no_enforcing.py. Вернуть 1 после порта system/sepolicy.\n'
    '    persist.a1000.selinux=0',
    '    # A1000/Android 10: политика портирована (_los17_selinux_q.py).\n'
    '    persist.a1000.selinux=1',
    '_los17_selinux_q'))

rw('rootdir/etc/a1000_selinux.rc', sub(
    'service a1000_selabel /system/bin/a1000_selabel.sh\n'
    '    class late_start\n'
    '    user root\n',
    'service a1000_selabel /system/bin/a1000_selabel.sh\n'
    '    class late_start\n'
    '    user root\n'
    '    # Android 10: без своего домена init под enforcing службу НЕ ЗАПУСТИТ,\n'
    '    # а второй проход снимает страховочный флаг. su в userdebug permissive —\n'
    '    # ему можно chcon и setenforce без отдельных правил.\n'
    '    seclabel u:r:su:s0\n',
    'seclabel u:r:su:s0'))

OLD_DEV = u'''# Графика: без этого у SurfaceFlinger и приложений нет ioctl к GPU.
# sprd_gsp — аппаратный масштабатор, к нему ходит сам SurfaceFlinger.
chcon u:object_r:gpu_device:s0 /dev/mali0
chcon u:object_r:gpu_device:s0 /dev/sprd_gsp 2>/dev/null
'''


def selabel(s):
    if 'ueventd' in s[:4000] and 'A1000/Android 10' in s:
        return s
    a = s.index(OLD_DEV)
    b = s.index(u'# ВНИМАНИЕ: -path в здешнем toybox')
    s = s[:a] + (u'# A1000/Android 10: узлы /dev (mali0, sprd_gsp, misc, трубы WCN, камера,\n'
                 u'# модем) метит ueventd по vendor/file_contexts в момент создания — это\n'
                 u'# надёжнее: HAL не успевают ткнуться в узел со старым типом. Прежние\n'
                 u'# chcon отсюда убраны (и /dev/mmcblk0p20 на десятке — это recovery).\n\n') + s[b:]
    old = u'        : > "$FLAG"\n        setenforce 1\n'
    assert s.count(old) == 1
    return s.replace(old, u'        : > "$FLAG"\n        setenforce 1\n'
                          u'        log -t a1000_selinux "enforcing: $(getenforce)"\n')


rw('rootdir/bin/a1000_selabel.sh', selabel)

rw('rootdir/etc/a1000_gps.rc', sub(
    '    mkdir /data/cg/supl 0770 gps system\n',
    '    mkdir /data/cg/supl 0770 gps system\n'
    '    # Тип a1000_gps_data_file (sepolicy/vendor/file_contexts); каталоги с\n'
    '    # прошлых прошивок лежат с system_data_file.\n'
    '    restorecon_recursive /data/cg\n',
    'restorecon_recursive /data/cg'))

rw('rootdir/etc/init/zram.rc', sub(
    'service zram_setup /system/bin/sh /system/bin/zram_setup.sh\n'
    '    user root\n',
    'service zram_setup /system/bin/sh /system/bin/zram_setup.sh\n'
    '    user root\n'
    '    # Скрипт шелла без своего домена: init десятки под enforcing такую\n'
    '    # службу не запускает. su (permissive в userdebug) — как у a1000_selabel.\n'
    '    seclabel u:r:su:s0\n',
    'seclabel u:r:su:s0'))
