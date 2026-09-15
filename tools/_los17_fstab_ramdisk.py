# -*- coding: utf-8 -*-
u"""A1000 / Android 10: положить fstab в ramdisk.

В десятке ramdisk в boot.img — только первая стадия (apex, dev, init, mnt,
proc, sys). Именно она обязана смонтировать раздел system и сделать
SwitchRoot("/system") — см. FirstStageMount::TrySwitchSystemAsRoot() в
system/core/init/first_stage_mount.cpp. Fstab она ищет либо в дереве устройств,
либо файлом /fstab.${ro.hardware} В САМОМ RAMDISK.

Наш device.mk клал fstab только в root/ (то есть внутрь образа system) и в
vendor/etc — до первой стадии он не доезжал, монтировать было нечего.

Кладём оба имени: sc8830 (приезжает из вшитой в ядро командной строки, см.
_los17_kernel_a10.sh) и unknown — на случай, если androidboot.hardware опять
потеряется, как это было на 8.1 и 9.
"""
import io

P = '/home/ard/los17/device/lenovo/a1000/device.mk'
MARK = 'ramdisk/fstab.sc8830'
s = io.open(P, encoding='utf-8').read()

if MARK in s:
    print(u'device.mk: fstab в ramdisk уже кладётся')
else:
    old = u'    $(LOCAL_PATH)/rootdir/etc/fstab.sc8830:root/fstab.sc8830 \\\n'
    assert old in s, u'не найдена строка копирования fstab в root'
    new = old + (
        u'    $(LOCAL_PATH)/rootdir/etc/fstab.sc8830:ramdisk/fstab.sc8830 \\\n'
        u'    $(LOCAL_PATH)/rootdir/etc/fstab.sc8830:ramdisk/fstab.unknown \\\n')
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'device.mk: fstab добавлен в ramdisk (sc8830 и unknown)')
