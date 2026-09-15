# -*- coding: utf-8 -*-
u"""A1000 / LOS 17.1: звук. Всплыло при включении Bluetooth — стек спрашивает у
политики звука форматы A2DP, и audioserver падал.

1. Политика звука. Десятка старый audio_policy.conf не читает вовсе, а XML ищет
   только в /odm/etc, /vendor/etc/audio и /vendor/etc. У нас XML был заглушкой
   ещё со времён первого запуска 8.1 и лежал в /system/etc — AudioPolicyManager
   садился на stub: модуля primary нет, звука нет, BT ронял audioserver
   (getHwOffloadEncodingFormatsSupportedForA2DP ищет модуль "primary").
   Новый XML — перевод стокового .conf (firmware/a1000_audio_q/).
2. setMasterMute/getMasterMute: стоковый audio.primary.sc8830.so объявляет
   указатель, но внутри валится с SIGSEGV. Та же правка, что на девятке
   (_los16_boot_fixes.py), только файл в десятке — Device.cpp.
"""
import io, os, shutil

T = '/home/ard/los17/'
D = T + 'device/lenovo/a1000/'
HERE = os.path.dirname(os.path.abspath(__file__))


def edit(path, old, new, mark):
    s = io.open(path, encoding='utf-8').read()
    if mark in s:
        print(path.replace(T, '') + u': уже правлен')
        return
    assert s.count(old) == 1, (path, old[:60])
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s.replace(old, new))
    print(path.replace(T, '') + u': правлен')


# ---- 1. политика звука ----
shutil.copy(os.path.join(HERE, 'a1000_audio_q', 'audio_policy_configuration.xml'),
            D + 'audio/audio_policy_configuration.xml')
print(u'audio/audio_policy_configuration.xml: из firmware/a1000_audio_q')

C = 'frameworks/av/services/audiopolicy/config/'
edit(D + 'device.mk',
     '''    $(LOCAL_PATH)/audio/audio_policy_configuration.xml:system/etc/audio_policy_configuration.xml \\
    frameworks/av/services/audiopolicy/config/stub_audio_policy_configuration.xml:system/etc/stub_audio_policy_configuration.xml \\
    frameworks/av/services/audiopolicy/config/audio_policy_volumes.xml:system/etc/audio_policy_volumes.xml \\
    frameworks/av/services/audiopolicy/config/default_volume_tables.xml:system/etc/default_volume_tables.xml''',
     '''    $(LOCAL_PATH)/audio/audio_policy_configuration.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio_policy_configuration.xml \\
    %sa2dp_audio_policy_configuration.xml:$(TARGET_COPY_OUT_VENDOR)/etc/a2dp_audio_policy_configuration.xml \\
    %susb_audio_policy_configuration.xml:$(TARGET_COPY_OUT_VENDOR)/etc/usb_audio_policy_configuration.xml \\
    %sr_submix_audio_policy_configuration.xml:$(TARGET_COPY_OUT_VENDOR)/etc/r_submix_audio_policy_configuration.xml \\
    %saudio_policy_volumes.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio_policy_volumes.xml \\
    %sdefault_volume_tables.xml:$(TARGET_COPY_OUT_VENDOR)/etc/default_volume_tables.xml''' % ((C,) * 5),
     'a2dp_audio_policy_configuration.xml')
# Комментарий над блоком врал («нет реального audio HW»).
edit(D + 'device.mk',
     '# stub audio_policy config (нет реального audio HW): top-level + include из frameworks/av\n',
     '# Политика звука: XML в /vendor/etc (Android 10 ищет только там, .conf не читает).\n'
     '# Перевод стокового audio_policy.conf, см. firmware/_los17_audio.py.\n',
     'Android 10 ищет только там')

# ---- 2. master mute ----
edit(T + 'hardware/interfaces/audio/core/all-versions/default/Device.cpp',
     '''Return<Result> Device::setMasterMute(bool mute) {
    Result retval(Result::NOT_SUPPORTED);
    if (mDevice->set_master_mute != NULL) {''',
     '''Return<Result> Device::setMasterMute(bool mute) {
    Result retval(Result::NOT_SUPPORTED);
    // A1000: стоковый audio.primary.sc8830.so указатель объявляет, но внутри
    // валится с SIGSEGV, а AudioFlinger зовёт это при старте. Проверки на NULL
    // здесь недостаточно — нужен явный отказ.
    if (property_get_bool("ro.audio.master_mute_broken", false)) {
        return retval;
    }
    if (mDevice->set_master_mute != NULL) {''',
     'master_mute_broken')
edit(T + 'hardware/interfaces/audio/core/all-versions/default/Device.cpp',
     '''    bool mute = false;
    if (mDevice->get_master_mute != NULL) {''',
     '''    bool mute = false;
    // A1000: см. setMasterMute — парная функция того же стокового HAL.
    if (property_get_bool("ro.audio.master_mute_broken", false)) {
        _hidl_cb(retval, mute);
        return Void();
    }
    if (mDevice->get_master_mute != NULL) {''',
     'парная функция того же стокового HAL')
edit(T + 'hardware/interfaces/audio/core/all-versions/default/Device.cpp',
     '#include <memory.h>\n', '#include <cutils/properties.h>\n#include <memory.h>\n',
     'cutils/properties.h')

P = D + 'system.prop'
s = io.open(P, encoding='utf-8').read()
if 'master_mute_broken' not in s:
    s += (u'\n# A1000: стоковый HAL звука валится в set_master_mute (SIGSEGV),\n'
          u'# а AudioFlinger зовёт её при старте. См. firmware/_los17_audio.py.\n'
          u'ro.audio.master_mute_broken=1\n')
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'system.prop: ro.audio.master_mute_broken=1')
