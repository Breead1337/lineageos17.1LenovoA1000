# -*- coding: utf-8 -*-
u"""A1000 / Android 10: пока НЕ включать SELinux enforcing.

Из журнала загрузки (снят в сырой раздел cache):
    avc: denied { create } for comm="a1000_selabel.s" name=".a1000_enforcing_try"
то есть a1000_selabel.sh дошёл до ветки перехода в enforcing и выполнил
setenforce 1. Дальше загрузка не жила.

Свойство persist.a1000.selinux=1 приехало из наработок 8.1/9 (device.mk), где
политика была доведена до enforcing. Для десятки политика ещё НЕ портирована —
по плану это самый большой кусок (593 строки в 42 файлах) и делается он ПОСЛЕ
первой успешной загрузки в permissive. До тех пор включать enforcing
бессмысленно: система просто не поднимется.

Метки узлов скрипт ставит ВЫШЕ этой ветки, они продолжают работать — выключаем
только сам переход.
"""
import io

P = '/home/ard/los17/device/lenovo/a1000/device.mk'
s = io.open(P, encoding='utf-8').read()

if 'persist.a1000.selinux=0' in s:
    print(u'device.mk: enforcing уже выключен')
else:
    old = u'    persist.a1000.selinux=1'
    assert old in s, u'не найдена строка persist.a1000.selinux'
    new = (u'    # A1000/Android 10: 0, пока не портирована политика SELinux.\n'
           u'    # С единицей a1000_selabel.sh делает setenforce 1 и загрузка умирает,\n'
           u'    # см. _los17_no_enforcing.py. Вернуть 1 после порта system/sepolicy.\n'
           u'    persist.a1000.selinux=0')
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'device.mk: persist.a1000.selinux = 0')
