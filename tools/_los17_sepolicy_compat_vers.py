# -*- coding: utf-8 -*-
u"""A1000 / Android 10: проверки совместимости sepolicy собирать НЕ версией 28.

secilc валится:
    libsepol.avtab_write_item: policy version 28 does not support ioctl
    extendedpermissions rules and one was specified
    Failed to write binary policy: -1
на цели out/.../treble_sepolicy_tests_28.0_intermediates/28.0_compat.

Свои .te от xperm-правил мы уже почистили (_los17_sepolicy_xperm.py), но здесь
в дело идут ПРЕДСОБРАННЫЕ CIL из system/sepolicy/prebuilts/api/28.0
(vendor_sepolicy.cil, plat_pub_versioned.cil) — их не почистить, да и не нужно:
это чисто сборочная проверка совместимости, её результат на устройство не
попадает. Наш POLICYVERS := 28 нужен ядру 3.10 для НАСТОЯЩЕЙ политики, а тесту
он ни к чему — собираем его штатной версией 30.
"""
import io

P = '/home/ard/los17/system/sepolicy/treble_sepolicy_tests_for_release.mk'
MARK = 'A1000_TEST_POLICYVERS'
s = io.open(P, encoding='utf-8').read()

if MARK in s:
    print(u'уже правлен')
else:
    head = (u'# A1000: цели этого файла — сборочные проверки, на устройство не едут.\n'
            u'# POLICYVERS у нас понижен до 28 ради ядра 3.10, но предсобранные CIL\n'
            u'# старых версий содержат xperm-правила, невыразимые в 28. Собираем\n'
            u'# проверки штатной версией.\n'
            u'A1000_TEST_POLICYVERS := 30\n\n')
    s = head + s.replace('$(POLICYVERS)', '$(A1000_TEST_POLICYVERS)')
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'treble_sepolicy_tests_for_release.mk: версия проверок 28 -> 30')
