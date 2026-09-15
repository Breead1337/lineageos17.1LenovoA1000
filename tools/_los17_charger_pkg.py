# -*- coding: utf-8 -*-
# LOS 17.1 / A1000: оффлайн-зарядка без анимации.
# animation.txt просит charger/lineage_battery_scale, lineage_percent_font,
# lineage_battery_fail, а в /res/images/charger лежат только AOSP-шные
# battery_scale/battery_fail: модуль lineage_charger_res_images (куда
# _los17_charger_res.py положил наши картинки) ставится ТОЛЬКО при
# WITH_LINEAGE_CHARGER=true, а мы его не задаём. Без картинки кадров
# healthd ставит num_frames=0 и рисует пустоту. Включаем один модуль —
# font_log/libhealthd.lineage не нужны, рисует AOSP-овый healthd.
import io
p = '/home/ard/los17/device/lenovo/a1000/device.mk'
s = io.open(p, encoding='utf-8').read()
old = '/charger/animation.txt:root/res/values/charger/animation.txt\n'
if 'lineage_charger_res_images' in s:
    print('device.mk: уже')
else:
    assert s.count(old) == 1
    s = s.replace(old, old + '# Картинки ставит модуль из vendor/lineage/charger (без него анимации нет).\n'
                  'PRODUCT_PACKAGES += lineage_charger_res_images\n')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('device.mk: lineage_charger_res_images добавлен')
