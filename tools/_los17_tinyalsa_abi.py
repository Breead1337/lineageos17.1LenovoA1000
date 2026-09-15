# -*- coding: utf-8 -*-
u"""A1000 / Android 10: НЕТ ЗВУКА и падение system_server при открытии настроек.

СИМПТОМ. Вендорный HAL звука по кругу не может открыть вывод:
    E audio_hw_primary: cannot open pcm_out driver: cannot set sw params: Invalid argument
    D audio_hw_primary: do_output_standby in
и так на каждый звук. Любой Ringtone в итоге висит в MediaPlayer.release()
дольше десяти секунд, после чего сторож финализатора ART убивает system_server:
    FATAL EXCEPTION IN SYSTEM PROCESS: FinalizerWatchdogDaemon
    java.util.concurrent.TimeoutException: android.media.Ringtone.finalize()
        timed out after 10 seconds
Снаружи это выглядит как «краш при открытии настроек Bluetooth» и как
«андроид завис» — перезапускается весь интерфейс.

ПРИЧИНА — расхождение ABI. `struct pcm_config` в tinyalsa обзавёлся полем
`silence_size` уже после Android 5, ровно между `silence_threshold` и
`avail_min`. Блоб `audio.primary.sc8830.so` собран под Android 5 и заполняет
СТАРУЮ структуру, а наш свежий libtinyalsa читает НОВУЮ: в `silence_size`
попадает чужой `avail_min`, а сам `avail_min` читается ЗА концом структуры
блоба — мусор. Ядро на такое отвечает EINVAL
(`snd_pcm_sw_params`: `if (params->avail_min == 0) return -EINVAL;` и проверки
silence_*).

На 8.1 этого не было: там в /system/lib подкладывалась СТОКОВАЯ libtinyalsa от
Android 5, и блоб разговаривал со своей же структурой. В девятке подкладывание
убрали — фреймворк требует символ mixer_subscribe_events, которого в стоковой
нет, — и ABI разъехалось.

ПРАВКА: вернуть структуре раскладку Android 5, убрав `silence_size`. В дереве
это поле не использует никто (только HAL'ы Qualcomm, которые тут не собираются),
а всё, что собирается, пересоберётся с той же короткой структурой — то есть
совпадёт и с блобом.
"""
import io, sys

H = '/home/ard/los17/external/tinyalsa/include/tinyalsa/asoundlib.h'
s = io.open(H, encoding='utf-8').read()
if 'unsigned int silence_size;' not in s:
    print('asoundlib.h: уже правлен')
else:
    old = u"""    unsigned int silence_threshold;
    unsigned int silence_size;
"""
    new = u"""    unsigned int silence_threshold;
    /* A1000: поля silence_size здесь НЕТ намеренно — оно появилось после
     * Android 5, а вендорный audio.primary.sc8830.so заполняет структуру
     * той эпохи. Подробности в _los16_tinyalsa_abi.py. */
"""
    assert old in s
    s = s.replace(old, new, 1)
    io.open(H, 'w', encoding='utf-8', newline='\n').write(s)
    print('asoundlib.h: silence_size убран')

P = '/home/ard/los17/external/tinyalsa/pcm.c'
s = io.open(P, encoding='utf-8').read()
old = u"    sparams.silence_size = config->silence_size;"
new = (u"    /* A1000: в структуре Android 5 такого поля нет — всегда ноль,\n"
       u"     * см. _los16_tinyalsa_abi.py. */\n"
       u"    sparams.silence_size = 0;")
if old in s:
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print('pcm.c: silence_size = 0')
else:
    print('pcm.c: уже правлен')
