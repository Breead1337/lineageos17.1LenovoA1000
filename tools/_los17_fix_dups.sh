#!/bin/bash
# Снимает конфликты «блоб из стока против модуля, собираемого из исходников»
# в дереве LOS 17.1. Идемпотентно, можно гонять после перекопирования vendor/.
V=/home/ard/los17/vendor/lenovo/a1000
# libdrmclearkeyplugin: в десятке собирается из frameworks/av/drm/.../clearkey/default
# и ставится по тому же пути → ckati «overriding commands for target».
sed -i '\#proprietary/vendor/lib/mediadrm/libdrmclearkeyplugin\.so#d' \
    $V/a1000-vendor.mk $V/a1000-vendor.mk.pre-bt 2>/dev/null
grep -c mediadrm $V/a1000-vendor.mk

# healthd.rc: у нас свой (class core вместо hal и без critical — это часть
# оффлайн-зарядки), но в десятке модуль healthd сам ставит свой .rc по тому же
# пути → «overriding commands». Кладём наш текст прямо в исходник и убираем
# копирование из device.mk.
T=/home/ard/los17
cp -f $T/device/lenovo/a1000/rootdir/etc/healthd.rc $T/system/core/healthd/healthd.rc
sed -i '\#rootdir/etc/healthd\.rc:system/etc/init/healthd\.rc#d' $T/device/lenovo/a1000/device.mk
grep -c healthd $T/device/lenovo/a1000/device.mk

# Картинки зарядки — вынесено в _los17_charger_res.py (наши png кладутся
# внутрь модуля vendor/lineage/charger, а не копируются мимо него).
