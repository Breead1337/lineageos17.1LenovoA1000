# -*- coding: utf-8 -*-
u"""A1000 / Android 10: доводка невыровненных доступов + adb в загруженной системе.

Система ЗАГРУЗИЛАСЬ (03.09.2026, до SetupWizard), но перезапускалась по кругу.
Из logcat загруженной системы — две отдельные поломки.

## 1. SIGBUS в SoundPool кладёт system_server и SystemUI

    F libc: Fatal signal 7 (SIGBUS), code 1 (BUS_ADRALN), fault addr 0xaca00045
            in tid (SoundPoolThread), pid 715 (system_server)
      #00 NuMediaExtractor::appendVorbisNumPageSamples(MediaBufferBase*, sp<ABuffer>)
      #01 NuMediaExtractor::readSampleData
      #03 android::Sample::doLoad()            (libsoundpool)

`appendVorbisNumPageSamples` дописывает четыре байта по адресу
`buffer->data() + mbuf->range_length()`, то есть по ПРОИЗВОЛЬНОМУ смещению;
компилятор разворачивает memcpy известного размера в одну инструкцию `str`.
На обычной кешируемой памяти ARMv7 такой доступ обслуживается аппаратно, а на
этом устройстве буфер приходит из некешируемой области (см.
[[a1000-uncached-ion-is-the-root]]) — для неё архитектура невыровненный доступ
НЕ обещает, прилетает alignment fault и SIGBUS.

Правка AOSP тут не поможет: таких мест в дереве много, а падает то одно, то
другое. У ядра ARM для этого есть штатный механизм — `/proc/cpu/alignment`:
    0 ignore, 1 warn, 2 fixup, 3 fixup+warn, 4 signal, 5 signal+warn
Ставим 2: ядро доэмулирует инструкцию вместо того, чтобы убивать процесс.
Медленнее, но это ровно то, для чего механизм и сделан.
# ponytail: чиним режимом ядра, а не правкой конкретного места в AOSP;
# если найдётся горячий путь, где доводка съедает заметное время, — искать
# конкретный источник некешируемого буфера.

## 2. adb в загруженной системе не поднимался

    I adbd: UsbFfs: connection terminated: failed to submit first read,
            AIO on FFS not supported
Асинхронный ввод-вывод в functionfs появился в ядрах с 3.18, у нас 3.10.
У adbd есть штатный переключатель на синхронный путь — свойство
`sys.usb.ffs.aio_compat`. На девятке это уже чинили (_los16_adb_aio.py),
в дерево десятки правку не перенесли.
"""
import io

D = '/home/ard/los17/device/lenovo/a1000/'

# ---------- 1. доводка невыровненных доступов ----------
P = D + 'rootdir/etc/a1000_cpu.rc'
s = io.open(P, encoding='utf-8').read()
if 'cpu/alignment' in s:
    print(u'a1000_cpu.rc: доводка уже включена')
else:
    s = s.rstrip('\n') + (
        u'\n\n'
        u'# A1000: некешируемые буферы этого SoC не переносят невыровненный доступ,\n'
        u'# и SoundPool валит system_server с SIGBUS (BUS_ADRALN). Просим ядро\n'
        u'# доэмулировать такие инструкции вместо убийства процесса.\n'
        u'# 2 = fixup; 3 добавляет запись в kmsg на каждый случай (для отладки).\n'
        u'on boot\n'
        u'    write /proc/cpu/alignment 2\n')
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'a1000_cpu.rc: write /proc/cpu/alignment 2')

# ---------- 2. adb без асинхронного functionfs ----------
P = D + 'system.prop'
s = io.open(P, encoding='utf-8').read()
if 'aio_compat' in s:
    print(u'system.prop: свойство adb уже есть')
else:
    s = s.rstrip('\n') + (
        u'\n\n'
        u'# A1000: ядро 3.10 не умеет асинхронный ввод-вывод в functionfs\n'
        u'# («AIO on FFS not supported»), и adbd не поднимает USB-транспорт вовсе.\n'
        u'# У adbd есть штатный синхронный путь, включается этим свойством.\n'
        u'sys.usb.ffs.aio_compat=true\n')
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'system.prop: sys.usb.ffs.aio_compat=true')
