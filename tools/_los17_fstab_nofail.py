# -*- coding: utf-8 -*-
u"""A1000 / Android 10: nofail для /cache и /productinfo, иначе НЕ СТАРТУЕТ zygote.

Журнал загрузки (сырой cache):
    init: fs_mgr_mount_all returned an error: Success
    init: Command 'mount_all /fstab.sc8830' ... failed: queue_fs_event() failed: Invalid code: 255

Разбор. В fs_mgr_mount_all (system/core/fs_mgr/fs_mgr.cpp:1310) КАЖДЫЙ не
смонтировавшийся раздел без флага no_fail даёт ++error_count, а на выходе
`if (error_count) return FS_MGR_MNTALL_FAIL;`. init получает -1 (в лог оно
приезжает как 255) и queue_fs_event() падает с «Invalid code», то есть НЕ
ставит `ro.crypto.state` и НЕ бросает триггер `nonencrypted`.

А в init.rc все ветки запуска zygote условны по этому свойству:
    on zygote-start && property:ro.crypto.state=unencrypted
        start zygote
Нет свойства — ни одна ветка не совпадает, `class_start main` не случается,
zygote не запускается НИКОГДА. Аппарат висит на лого.

Почему раньше это не било в глаза: zygote всё-таки стартовал — но только как
побочный эффект падений surfaceflinger, у которого в surfaceflinger.rc стоит
`onrestart restart zygote`. Как только SF починили (встал mali.ko), «случайный»
запуск zygote пропал и загрузка встала намертво. Классическая ловушка: чинишь
одно — вскрывается то, что всё это время держалось на костыле.

Не монтируются два раздела, и оба — законно:
  * /cache — мы САМИ затираем его сырым журналом загрузки (_a1000_earlylog.rc),
    ext4 там больше нет: «Invalid ext4 superblock»;
  * /productinfo (prodnv) — в system-as-root нет точки монтирования: каталога
    /productinfo в образе system просто не существует («target=(missing)»).
    Форматировать prodnv НЕЛЬЗЯ, там NV модема (IMEI), поэтому только nofail.

Ни один из них для загрузки не нужен, поэтому помечаем оба `nofail`.
"""
import io

P = '/home/ard/los17/device/lenovo/a1000/rootdir/etc/fstab.sc8830'
s = io.open(P, encoding='utf-8').read()

n = 0
for mp in ('/cache', '/productinfo'):
    out = []
    for line in s.split('\n'):
        parts = line.split()
        if len(parts) >= 5 and parts[1] == mp and 'nofail' not in parts[4]:
            line = line.replace(parts[4], parts[4] + ',nofail', 1)
            n += 1
        out.append(line)
    s = '\n'.join(out)

if n:
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'fstab.sc8830: nofail добавлен, строк изменено: %d' % n)
else:
    print(u'fstab.sc8830: nofail уже стоит')
