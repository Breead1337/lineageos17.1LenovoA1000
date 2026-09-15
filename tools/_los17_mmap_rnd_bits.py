# -*- coding: utf-8 -*-
u"""A1000 / Android 10: не убивать init из-за отсутствующего mmap_rnd_bits.

Из лога упавшей загрузки (ramoops):
    init: Cannot open for reading: /proc/sys/vm/mmap_rnd_bits
    init: Unable to set adequate mmap entropy value!
дальше LOG(FATAL) -> паника -> аппарат уходит в фастбут.

Ручка /proc/sys/vm/mmap_rnd_bits появилась вместе с ARCH_MMAP_RND_BITS в ядрах
4.x (коммиты перечислены в самом security.cpp: e0c25d958f78 для arm). В нашем
3.10 её нет и взяться неоткуда — бэкпортить рандомизацию ради одной проверки
смысла нет.

Правка: если ручки в ядре НЕТ вообще — предупреждаем и идём дальше. Если она
есть, но значение выставить не удалось, поведение прежнее (FATAL): это уже
настоящая ошибка, а не старое ядро.

Теряем: рандомизацию адресного пространства настраивает ядро своим умолчанием
(ARCH_MMAP_RND_BITS в 3.10 не настраивается, работает штатный ASLR).
"""
import io

P = '/home/ard/los17/system/core/init/security.cpp'
MARK = 'A1000: ядро 3.10 не знает про mmap_rnd_bits'
s = io.open(P, encoding='utf-8').read()

if MARK in s:
    print(u'security.cpp: уже правлен')
else:
    old = u'Result<Success> SetMmapRndBitsAction(const BuiltinArguments&) {\n'
    assert old in s, u'не найдено начало SetMmapRndBitsAction'
    new = old + (
        u'    /* ' + MARK + u': ручка /proc/sys/vm/mmap_rnd_bits\n'
        u'     * появилась с ARCH_MMAP_RND_BITS в 4.x (см. список коммитов ниже).\n'
        u'     * Раз её нет вовсе — это старое ядро, а не сбой: предупреждаем и\n'
        u'     * продолжаем. Если ручка есть, но записать не вышло — прежний FATAL. */\n'
        u'    if (access(MMAP_RND_PATH, F_OK) != 0 && access(MMAP_RND_COMPAT_PATH, F_OK) != 0) {\n'
        u'        LOG(WARNING) << "mmap_rnd_bits: ядро не поддерживает, пропускаем";\n'
        u'        return Success();\n'
        u'    }\n')
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'security.cpp: отсутствие mmap_rnd_bits больше не фатально')
