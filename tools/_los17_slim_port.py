# -*- coding: utf-8 -*-
# LOS 17.1: перенос блока A1000_SLIM под правила Android 10.
#
# В десятке продуктовые переменные после разбора продукта помечены .KATI_READONLY,
# поэтому прежний приём из 8.1 (правим PRODUCT_LOCALES/PRODUCT_COPY_FILES прямо
# в BoardConfig.mk) валится с "cannot assign to readonly variable".
#
# Что делаем:
#   * PRODUCT_LOCALES / PRODUCT_AAPT_* переезжают в продуктовый lineage_a1000.mk;
#   * фильтры пакетов и pico-голосов правят карту PRODUCTS.<продукт>.* — она
#     readonly НЕ помечена, значит приём 8.1 остаётся рабочим.
import io

D = '/home/ard/los17/device/lenovo/a1000/'
B, P = D + 'BoardConfig.mk', D + 'lineage_a1000.mk'

b = io.open(B, encoding='utf-8').read()
if 'A10: локали переехали' not in b:
    old_loc = """PRODUCT_LOCALES := en_US ru_RU
PRODUCT_AAPT_CONFIG := en_US ru_RU normal hdpi
PRODUCT_AAPT_PREF_CONFIG := hdpi"""
    new_loc = """# A10: локали переехали в lineage_a1000.mk — в десятке PRODUCT_* здесь readonly."""
    assert old_loc in b, 'блок локалей не найден'
    b = b.replace(old_loc, new_loc, 1)

    old_ovl = "PRODUCT_PACKAGE_OVERLAYS := $(filter-out vendor/lineage/overlay/dictionaries,$(PRODUCT_PACKAGE_OVERLAYS))"
    new_ovl = ("PRODUCTS.$(INTERNAL_PRODUCT).PRODUCT_PACKAGE_OVERLAYS := $(filter-out \\n"
               "    vendor/lineage/overlay/dictionaries,$(PRODUCTS.$(INTERNAL_PRODUCT).PRODUCT_PACKAGE_OVERLAYS))")
    assert old_ovl in b, 'блок словарей не найден'
    b = b.replace(old_ovl, new_ovl, 1)

    old_pico = "PRODUCT_COPY_FILES := $(filter-out external/svox/pico/lang/%,$(PRODUCT_COPY_FILES))"
    new_pico = ("PRODUCTS.$(INTERNAL_PRODUCT).PRODUCT_COPY_FILES := $(filter-out \\n"
                "    external/svox/pico/lang/%,$(PRODUCTS.$(INTERNAL_PRODUCT).PRODUCT_COPY_FILES))")
    assert old_pico in b, 'блок pico не найден'
    b = b.replace(old_pico, new_pico, 1)
    io.open(B, 'w', encoding='utf-8').write(b)
    print('BoardConfig.mk: блок SLIM переведён на карту PRODUCTS.*')
else:
    print('BoardConfig.mk: уже правлен')

p = io.open(P, encoding='utf-8').read()
if 'A1000_SLIM: локали' not in p:
    p += """
# ---- A1000_SLIM: локали (в десятке задаются только в продуктовом файле) ----
# Было ~120 локалей (ресурсы в каждом apk), стало две.
PRODUCT_LOCALES := en_US ru_RU
PRODUCT_AAPT_CONFIG := en_US ru_RU normal hdpi
PRODUCT_AAPT_PREF_CONFIG := hdpi
"""
    io.open(P, 'w', encoding='utf-8').write(p)
    print('lineage_a1000.mk: локали добавлены')
else:
    print('lineage_a1000.mk: уже правлен')
