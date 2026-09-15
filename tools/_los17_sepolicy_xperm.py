# -*- coding: utf-8 -*-
# LOS 17.1 / A1000: убрать из sepolicy правила расширенных прав (xperm).
#
# checkpolicy валится: "policy version 28 does not support ioctl
# extendedpermissions rules". Версия 28 у нас не от хорошей жизни — ядро 3.10
# старше самой возможности: фильтрация ioctl по номерам (allowxperm) появилась
# в SELinux ядра 4.3, и policydb версии 30. Поднять версию нельзя — ядро
# такую политику просто не загрузит.
#
# Делаем то же, что на 8.1 и 9: вырезаем сами xperm-правила. Потеря — только
# более тонкая фильтрация ioctl; обычные allow остаются на месте.
#
# Правило может занимать несколько строк, поэтому режем от ключевого слова до
# строки с точкой с запятой. В отличие от версии для девятки файлы ищем по
# всему дереву: в десятке .te лежат ещё и в vendor/lineage, device/ и
# prebuilts/api.
import io, os, subprocess

T = '/home/ard/los17'
KEYS = ('allowxperm', 'neverallowxperm', 'auditallowxperm', 'dontauditxperm')
NOTE = '# A1000: правило xperm убрано — ядру 3.10 нужна policydb 28 без них' + chr(10)

find = subprocess.Popen(
    ['grep', '-rl', '--include=*.te', '--include=te_macros', '-e', 'xperm',
     T + '/system/sepolicy', T + '/device/lenovo', T + '/vendor/lineage',
     T + '/hardware', T + '/bootable'],
    stdout=subprocess.PIPE)
paths = [p for p in find.communicate()[0].decode('utf-8').split('\n') if p]

changed = files = 0
for path in paths:
    if '/tests/' in path:
        continue
    lines = io.open(path, encoding='utf-8').readlines()
    out, i, hit = [], 0, 0
    while i < len(lines):
        s = lines[i].lstrip()
        if s.startswith(KEYS):
            hit += 1
            while i < len(lines) and ';' not in lines[i]:
                i += 1
            i += 1
            out.append(NOTE)
            continue
        out.append(lines[i])
        i += 1
    if hit:
        io.open(path, 'w', encoding='utf-8').writelines(out)
        files += 1
        changed += hit
print('вырезано правил: %d в %d файлах' % (changed, files))
