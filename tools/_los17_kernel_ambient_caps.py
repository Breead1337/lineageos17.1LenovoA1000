# -*- coding: utf-8 -*-
u"""A1000 / Android 10: бэкпорт ambient capabilities в ядро 3.10.

ЗАЧЕМ. Журнал зависшей загрузки (снят в сырой раздел cache) сказал прямо:
    init: /system/etc/init/logd.rc: 9: capabilities requested but the kernel
          does not support ambient capabilities
    logd: failed to set CAP_SETGID, CAP_SYSLOG or CAP_AUDIT_CONTROL (1)
    init: Service 'logd' (pid 531) exited with status 1
и так по кругу. Тем же затронуты lmkd, audioserver, incidentd, bpfloader,
mtpd, racoon, android.system.suspend, наши a1000_bt.rc и a1000_ril.rc.

В десятке init раздаёт службам права ТОЛЬКО через ambient-набор: служба
работает не от root, а нужные CAP_* должны пережить exec. Механизм появился в
ядре 4.3 (коммит 58319057b784 "capabilities: ambient capabilities"), в 3.10
его нет — значит ни одна такая служба прав не получает. logd падает, init его
перезапускает, загрузка не двигается. Это не настроечная мелочь вроде
mmap_rnd_bits: без ambient модель привилегий десятки не работает вовсе.

ЧТО ДЕЛАЕМ (перенос по апстриму, минимально необходимый набор):
  1. prctl.h        — номер PR_CAP_AMBIENT и его подкоманды;
  2. cred.h         — поле cap_ambient в struct cred;
  3. cred.c         — пустой ambient у init_cred (копирование в prepare_creds
                      и copy_creds идёт memcpy'ем всей структуры, править не надо);
  4. commoncap.c    — инвариант pA ⊆ (pP ∩ pI) в cap_capset и перенос
                      ambient через exec в cap_bprm_set_creds;
  5. sys.c          — сама операция prctl(PR_CAP_AMBIENT, ...).

Securebit SECURE_NO_CAP_AMBIENT_RAISE намеренно НЕ переносим: он нужен только
тем, кто хочет запретить raise, Android им не пользуется, а лишние правки в
securebits — лишний риск.
"""
import io

K = '/home/ard/a1000-kernel'


def patch(path, anchor, addition, mark, after=True):
    p = K + '/' + path
    s = io.open(p, encoding='utf-8', errors='surrogateescape').read()
    if mark in s:
        print(u'%s: уже правлен' % path)
        return
    assert anchor in s, u'%s: не найден якорь' % path
    s = s.replace(anchor, (anchor + addition) if after else (addition + anchor), 1)
    io.open(p, 'w', encoding='utf-8', errors='surrogateescape', newline='\n').write(s)
    print(u'%s: правка внесена' % path)


# 1. prctl.h -----------------------------------------------------------------
patch('include/uapi/linux/prctl.h',
      '#endif /* _LINUX_PRCTL_H */',
      '',
      'PR_CAP_AMBIENT')
# вставка ДО #endif делается отдельно, иначе попадём за пределы заголовка
p = K + '/include/uapi/linux/prctl.h'
s = io.open(p, encoding='utf-8', errors='surrogateescape').read()
if 'PR_CAP_AMBIENT' not in s:
    s = s.replace('#endif /* _LINUX_PRCTL_H */',
                  '/* A1000: ambient capabilities, бэкпорт из 4.3 (58319057b784).\n'
                  ' * Без них init десятки не может раздать права службам. */\n'
                  '#define PR_CAP_AMBIENT\t\t\t47\n'
                  '# define PR_CAP_AMBIENT_IS_SET\t\t1\n'
                  '# define PR_CAP_AMBIENT_RAISE\t\t2\n'
                  '# define PR_CAP_AMBIENT_LOWER\t\t3\n'
                  '# define PR_CAP_AMBIENT_CLEAR_ALL\t4\n\n'
                  '#endif /* _LINUX_PRCTL_H */', 1)
    io.open(p, 'w', encoding='utf-8', errors='surrogateescape', newline='\n').write(s)
    print(u'prctl.h: добавлен PR_CAP_AMBIENT')

# 2. cred.h ------------------------------------------------------------------
patch('include/linux/cred.h',
      '\tkernel_cap_t\tcap_bset;\t/* capability bounding set */',
      '\n\tkernel_cap_t\tcap_ambient;\t/* A1000: ambient capability set */',
      'cap_ambient')

# 3. cred.c ------------------------------------------------------------------
patch('kernel/cred.c',
      '\t.cap_bset\t\t= CAP_FULL_SET,',
      '\n\t.cap_ambient\t\t= CAP_EMPTY_SET,',
      'cap_ambient')

# 4. commoncap.c -------------------------------------------------------------
# 4a. инвариант при capset
patch('security/commoncap.c',
      '\tnew->cap_effective   = *effective;\n'
      '\tnew->cap_inheritable = *inheritable;\n'
      '\tnew->cap_permitted   = *permitted;\n',
      '\t/* A1000: ambient обязан оставаться подмножеством pP ∩ pI. */\n'
      '\tnew->cap_ambient     = cap_intersect(old->cap_ambient,\n'
      '\t\t\t\t\t     cap_intersect(*permitted,\n'
      '\t\t\t\t\t\t\t   *inheritable));\n',
      'cap_ambient')

# 4b. перенос через exec
patch('security/commoncap.c',
      '\tbprm->cap_effective = effective;\n',
      '\n'
      '\t/* A1000: ambient переживает exec и добавляется к pP и pE. Если файл\n'
      '\t * сам даёт привилегии (file caps) или меняет uid/gid, ambient\n'
      '\t * сбрасываем — как в апстриме, иначе это дыра. */\n'
      '\tif (has_cap || !uid_eq(new->euid, old->euid) ||\n'
      '\t    !gid_eq(new->egid, old->egid)) {\n'
      '\t\tcap_clear(new->cap_ambient);\n'
      '\t} else {\n'
      '\t\tnew->cap_permitted = cap_combine(new->cap_permitted,\n'
      '\t\t\t\t\t\t new->cap_ambient);\n'
      '\t\tnew->cap_effective = cap_combine(new->cap_effective,\n'
      '\t\t\t\t\t\t new->cap_ambient);\n'
      '\t}\n',
      'cap_ambient')

# 5. sys.c -------------------------------------------------------------------
patch('kernel/sys.c',
      '\tcase PR_SET_TIMERSLACK:',
      '',
      'PR_CAP_AMBIENT')
p = K + '/kernel/sys.c'
s = io.open(p, encoding='utf-8', errors='surrogateescape').read()
if 'PR_CAP_AMBIENT' not in s:
    case = (
        '\tcase PR_CAP_AMBIENT: {\n'
        '\t\t/* A1000: бэкпорт из 4.3 (58319057b784). Поднять право в ambient\n'
        '\t\t * можно, только если оно уже есть и в permitted, и в inheritable. */\n'
        '\t\tstruct cred *new_cred;\n'
        '\n'
        '\t\tif (arg2 == PR_CAP_AMBIENT_CLEAR_ALL) {\n'
        '\t\t\tif (arg3 | arg4 | arg5)\n'
        '\t\t\t\treturn -EINVAL;\n'
        '\t\t\tnew_cred = prepare_creds();\n'
        '\t\t\tif (!new_cred)\n'
        '\t\t\t\treturn -ENOMEM;\n'
        '\t\t\tcap_clear(new_cred->cap_ambient);\n'
        '\t\t\treturn commit_creds(new_cred);\n'
        '\t\t}\n'
        '\n'
        '\t\tif (((!cap_valid(arg3)) | arg4 | arg5))\n'
        '\t\t\treturn -EINVAL;\n'
        '\n'
        '\t\tif (arg2 == PR_CAP_AMBIENT_IS_SET) {\n'
        '\t\t\terror = !!cap_raised(current_cred()->cap_ambient, arg3);\n'
        '\t\t\tbreak;\n'
        '\t\t}\n'
        '\n'
        '\t\tif (arg2 != PR_CAP_AMBIENT_RAISE &&\n'
        '\t\t    arg2 != PR_CAP_AMBIENT_LOWER)\n'
        '\t\t\treturn -EINVAL;\n'
        '\n'
        '\t\tif (arg2 == PR_CAP_AMBIENT_RAISE &&\n'
        '\t\t    (!cap_raised(current_cred()->cap_permitted, arg3) ||\n'
        '\t\t     !cap_raised(current_cred()->cap_inheritable, arg3)))\n'
        '\t\t\treturn -EPERM;\n'
        '\n'
        '\t\tnew_cred = prepare_creds();\n'
        '\t\tif (!new_cred)\n'
        '\t\t\treturn -ENOMEM;\n'
        '\t\tif (arg2 == PR_CAP_AMBIENT_RAISE)\n'
        '\t\t\tcap_raise(new_cred->cap_ambient, arg3);\n'
        '\t\telse\n'
        '\t\t\tcap_lower(new_cred->cap_ambient, arg3);\n'
        '\t\treturn commit_creds(new_cred);\n'
        '\t}\n')
    s = s.replace('\tcase PR_SET_TIMERSLACK:', case + '\tcase PR_SET_TIMERSLACK:', 1)
    io.open(p, 'w', encoding='utf-8', errors='surrogateescape', newline='\n').write(s)
    print(u'sys.c: добавлена операция PR_CAP_AMBIENT')
