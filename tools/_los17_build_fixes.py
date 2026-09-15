# -*- coding: utf-8 -*-
u"""A1000 / Android 10: мелкие правки, без которых не собирается.
Идемпотентно — можно гонять повторно.

1. USE_XML_AUDIO_POLICY_CONF. В десятке AudioPolicyManager.cpp намеренно
   ломает сборку (#error «Audio policy no longer supports legacy .conf»), если
   флаг не выставлен. Флаг живёт в BoardConfigMainlineCommon.mk, который наш
   старый BoardConfig не включает. XML у нас давно есть
   (device/lenovo/a1000/audio/audio_policy_configuration.xml), так что просто
   объявляем флаг.

2. libfmjni. В десятке к JNI-модулю приезжают -W -Wall -Werror, а libfm_jni.cpp
   апстримный и не использует env/thiz в двух десятках функций. Гасим ровно эти
   предупреждения, а не -Werror целиком.
"""
import io

T = '/home/ard/los17'


def ensure(path, marker, text, where=None):
    s = io.open(path, encoding='utf-8').read()
    if marker in s:
        print(u'%s: уже правлен' % path.split('/')[-1])
        return
    if where is None:
        s = s.rstrip('\n') + '\n' + text
    else:
        assert where in s, where
        s = s.replace(where, where + text, 1)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'%s: правка внесена' % path.split('/')[-1])


ensure(T + '/device/lenovo/a1000/BoardConfig.mk',
       'USE_XML_AUDIO_POLICY_CONF',
       u'\n# A1000: в десятке .conf-формат политики звука запрещён на уровне #error.\n'
       u'# XML лежит в device/lenovo/a1000/audio/audio_policy_configuration.xml.\n'
       u'USE_XML_AUDIO_POLICY_CONF := 1\n')

ensure(T + '/packages/apps/FMRadio/jni/fmr/Android.mk',
       'Wno-unused-parameter',
       u'\n# A1000: апстримный libfm_jni.cpp не использует env/thiz в двух десятках\n'
       u'# функций, а в десятке к модулю приезжает -Werror. Гасим точечно.\n'
       u'LOCAL_CFLAGS += -Wno-unused-parameter -Wno-unused-variable\n',
       where='LOCAL_MODULE := libfmjni\n')
