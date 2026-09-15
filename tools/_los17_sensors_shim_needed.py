# -*- coding: utf-8 -*-
u"""A1000 / Android 10: вписать шим сенсоров в DT_NEEDED блоба.

ЗАЧЕМ. system_server вечно ждёт сенсоры и его убивает watchdog:
    Watchdog: main annotated stack trace:
        ConcurrentUtils.waitForFutureNoInterrupt
        SystemServer.startOtherServices(SystemServer.java:1041)   <- ждёт StartSensorService
    E vndksupport: Could not load /vendor/lib/hw/sensors.sc8830.so from default
        namespace: dlopen failed: cannot locate symbol "android_atomic_release_cas"

`android_atomic_release_cas` экспортировался libcutils до Android 8, потом стал
inline. Шим на это написан (external/libsprdsensors_shim) и установлен как
/vendor/lib/libsprdsensors_shim.so.

ПОЧЕМУ НЕ LD_PRELOAD. В дереве 8.1 шим цеплялся строкой
`setenv LD_PRELOAD libsprdsensors_shim.so` в rc сервиса. На десятке это НЕ
РАБОТАЕТ (проверено живьём: сообщение об отсутствующем символе осталось
слово в слово, а сам libsprdsensors_shim в логе не упоминается ни разу) —
блоб грузится через vndksupport/android_load_sphal_library, и preload
default-пространства до него не долетает.

Рабочий способ на этом устройстве — тот же, что уже применён к графике:
у gralloc.sc8830.so и hwcomposer.sc8830.so libui_shim.so стоит прямо в
DT_NEEDED. Делаем то же самое для сенсоров.
"""
import os
import subprocess

B = '/home/ard/los17/vendor/lenovo/a1000/proprietary/lib/hw/sensors.sc8830.so'
SHIM = 'libsprdsensors_shim.so'

out = subprocess.check_output(['readelf', '-d', B]).decode('utf-8', 'replace')
if SHIM in out:
    print(u'sensors.sc8830.so: шим уже в DT_NEEDED')
else:
    bak = B + '.pre-shim'
    if not os.path.exists(bak):
        subprocess.check_call(['cp', '-p', B, bak])
    subprocess.check_call(['patchelf', '--add-needed', SHIM, B])
    out = subprocess.check_output(['readelf', '-d', B]).decode('utf-8', 'replace')
    assert SHIM in out, u'patchelf не добавил зависимость'
    print(u'sensors.sc8830.so: %s вписан в DT_NEEDED' % SHIM)
