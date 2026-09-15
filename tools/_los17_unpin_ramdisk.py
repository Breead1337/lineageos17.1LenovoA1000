# -*- coding: utf-8 -*-
u"""A1000 / Android 10: снять прибитый гвоздями ramdisk с boot.img.

В BoardConfig.mk стояло:
    BOARD_MKBOOTIMG_ARGS := ... --dt .../sprd.dtb --ramdisk .../prebuilt/ramdisk.img

`--ramdisk` в аргументах mkbootimg ПЕРЕКРЫВАЕТ ramdisk, который делает сборка:
в boot.img уезжал файл от 24.08 эпохи 8.1/9 (2 195 702 байта) вместо
свежего (807 735). Внутри него init от Oreo — в бинарнике видна строка
`system/core/init/init_first_stage.cpp`, в десятке этот файл называется
first_stage_init.cpp.

Последствие ровно то, что мы ловили: старый init монтирует раздел в /system,
а образ десятки — система-как-корень, поэтому настоящие файлы оказываются в
/system/system/, запускать нечего. Снаружи — зависание на лого либо белый
экран, без adb.

Прибили ramdisk во времена LOS 16 (см. память a1000-los16-ramdisk-pinned),
потому что правки rootdir не доезжали. Для десятки это смертельно: init обязан
быть свой. `--dt` ОСТАВЛЯЕМ — без дерева устройств загрузчик SC8830 образ не
берёт вовсе (проверено: у всех рабочих образов поле dt_size = 53248, у собранных
без него — 0, и они не грузятся).
"""
import io

P = '/home/ard/los17/device/lenovo/a1000/BoardConfig.mk'
BS = chr(92)
s = io.open(P, encoding='utf-8').read()
lines = s.split('\n')

out, changed = [], False
for i, l in enumerate(lines):
    if '--ramdisk' in l and 'prebuilt/ramdisk.img' in l:
        changed = True
        # предыдущая строка теряет продолжение, если эта была последней в списке
        if out and out[-1].rstrip().endswith(BS):
            out[-1] = out[-1].rstrip()[:-1].rstrip()
        out.append('# A1000/Android 10: --ramdisk НЕ задаём — mkbootimg должен взять')
        out.append('# ramdisk, собранный деревом. Прибитый файл от 8.1/9 нёс init от Oreo,')
        out.append('# и десятка не грузилась. Подробности в _los17_unpin_ramdisk.py.')
        continue
    out.append(l)

if not changed:
    print(u'BoardConfig.mk: прибитого ramdisk нет, уже снят')
else:
    io.open(P, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
    print(u'BoardConfig.mk: прибитый ramdisk снят, --dt оставлен')
