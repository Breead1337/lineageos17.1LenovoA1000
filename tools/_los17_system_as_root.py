# -*- coding: utf-8 -*-
u"""A1000 / Android 10: включить system-as-root — иначе зависание на лого.

В десятке build_image.py собирает образ system ВСЕГДА как system-as-root:
корневая ФС (init, init.rc, fstab, контексты) плюс каталог system/ внутри.
Это безусловно, см. build/make/tools/releasetools/build_image.py:
    root_dir = prop_dict.get("root_dir")
    if root_dir: shutil.copytree(root_dir, in_dir, symlinks=True)
    in_dir_system = os.path.join(in_dir, "system")
и root_dir= пишется в system_image_info.txt без всяких условий.

Без BOARD_BUILD_SYSTEM_ROOT_IMAGE boot.img собирается по-старому: полный
ramdisk-корень, init монтирует раздел в /system по fstab — и настоящие файлы
оказываются на уровень глубже (/system/system/bin/...). Запускать нечего,
аппарат стоит на лого.

С флагом ramdisk становится первой стадией и делает switch_root в раздел —
форма образа и способ загрузки совпадают. Загрузчик трогать не нужно:
skip_initramfs не требуется, переключением занимается сам init.
"""
import io

P = '/home/ard/los17/device/lenovo/a1000/BoardConfig.mk'
MARK = 'BOARD_BUILD_SYSTEM_ROOT_IMAGE'
s = io.open(P, encoding='utf-8').read()

if MARK in s:
    print(u'BoardConfig.mk: уже правлен')
else:
    s = s.rstrip('\n') + (
        u'\n\n# A1000: в десятке образ system ВСЕГДА система-как-корень (см.\n'
        u'# _los17_system_as_root.py). Без этого флага boot.img собирается со\n'
        u'# старым полным ramdisk и монтирует раздел в /system — файлы уезжают\n'
        u'# в /system/system/, запускать нечего, аппарат стоит на лого.\n'
        u'BOARD_BUILD_SYSTEM_ROOT_IMAGE := true\n')
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'BoardConfig.mk: BOARD_BUILD_SYSTEM_ROOT_IMAGE := true')
