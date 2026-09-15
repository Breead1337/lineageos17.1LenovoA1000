# -*- coding: utf-8 -*-
u"""A1000 / LOS 17.1: Bluetooth.

1. system/bt — патч 8.1 (los17_system_bt.patch, снят git diff'ом с дерева 17.1):
   * future для VSC 0xFD53: чип отвечает Command Status, апстрим выбрасывал
     событие, и старт controller_module висел вечно (BT не включался вообще);
   * KNOB: Read Encryption Key Size чип 2.1+EDR не знает — флаг вместо FATAL;
   * LE в чипе нет: CHECK(ble_supported) -> ранний выход (в десятке к 8.1-м
     добавился get_ble_maximum_tx_data_length), LE Rand — из /dev/urandom.
2. a1000_bt.rc: из 8.1 приехали mkdir /data/misc/bluetooth{,/logs} с владельцем
   system:system — они перебивали правильные bluetooth:bluetooth из init.rc
   десятки, и стек не мог писать btsnoop. Строки удалены (init.rc делает сам).
"""
import io, os, subprocess

T = '/home/ard/los17/'
HERE = os.path.dirname(os.path.abspath(__file__))

bt = T + 'system/bt'
if 'status_given_to_future' in io.open(bt + '/hci/src/hci_layer.cc', encoding='utf-8').read():
    print(u'system/bt: патч уже наложен')
else:
    subprocess.check_call(['git', 'apply', os.path.join(HERE, 'los17_system_bt.patch')], cwd=bt)
    print(u'system/bt: los17_system_bt.patch наложен')

P = T + 'device/lenovo/a1000/rootdir/etc/a1000_bt.rc'
s = io.open(P, encoding='utf-8').read()
old = ('    mkdir /data/misc/bluedroid 0770 bluetooth \n'
       '    mkdir /data/misc/bluetooth 0770 system system\n'
       '    mkdir /data/misc/bluetooth/logs 0770 system system\n')
if old in s:
    s = s.replace(old, '    # /data/misc/bluedroid и /data/misc/bluetooth{,/logs} создаёт init.rc\n'
                       '    # десятки с владельцем bluetooth. Прежние строки 8.1 (system:system)\n'
                       '    # перебивали его — стек не мог писать btsnoop.\n')
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'a1000_bt.rc: mkdir каталогов BT убраны')
else:
    print(u'a1000_bt.rc: уже правлен')
