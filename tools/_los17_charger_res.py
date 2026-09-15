# -*- coding: utf-8 -*-
u"""A1000 / Android 10: картинки экрана зарядки.

В дереве наши картинки лежали двумя копиями сразу: в device/lenovo/a1000/charger
(копирование через PRODUCT_COPY_FILES) и в vendor/lineage/charger/images/hdpi
(модули vendor_lineage_charger_*.png). Правило установки у модуля рождается
всегда, даже если модуль не попал в PRODUCT_PACKAGES, поэтому ckati падал:
    overriding commands for target root/res/images/charger/lineage_battery_scale.png

Наши картинки взяты из ветки lineage-20.0 и крупнее: lineage_battery_scale
43 КБ против 10 КБ в 17.1, а lineage_battery_fail и lineage_percent_font в
17.1 отсутствуют вовсе — под них написан наш animation.txt. Поэтому не
выбрасываем свои, а КЛАДЁМ их в images/hdpi самого модуля и убираем
копирование из device.mk. animation.txt остаётся копированием: он едет в
root/res/values/charger, туда модуль ничего не ставит.
"""
import io, os, shutil, glob

T = '/home/ard/los17'
SRC = T + '/device/lenovo/a1000/charger'
DST = T + '/vendor/lineage/charger/images/hdpi'

for name in ('lineage_battery_scale.png', 'lineage_battery_fail.png',
             'lineage_percent_font.png'):
    src = os.path.join(SRC, name)
    if os.path.isfile(src):
        shutil.copyfile(src, os.path.join(DST, name))
        print(u'в модуль: %s' % name)

# убираем копирование картинок (но НЕ animation.txt) из device.mk
BS = chr(92)
p = T + '/device/lenovo/a1000/device.mk'
lines = io.open(p, encoding='utf-8').read().split('\n')
def is_img_copy(l):
    return '/charger/' in l and l.rstrip().rstrip(BS).rstrip().endswith('.png')
out = [l for l in lines if not is_img_copy(l)]
if out != lines:
    for i, l in enumerate(out):
        if l.rstrip().endswith(BS) and (i + 1 >= len(out) or out[i + 1].strip() == ''):
            out[i] = l.rstrip()[:-1].rstrip()
    io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
    print(u'device.mk: копирование картинок зарядки убрано')
else:
    print(u'device.mk: уже без копирования картинок')
