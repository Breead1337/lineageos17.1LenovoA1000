# -*- coding: utf-8 -*-
u"""Убрать из mk'шек A1000 строку PRODUCT_COPY_FILES с заданным назначением.
Аргумент — путь назначения (например system/lib/libtinyalsa.so).
Заодно чинит повисшую обратную косую на последней строке списка."""
import io, sys, glob

BS = chr(92)  # обратная косая; в исходнике её нет намеренно — heredoc её ест
dest = sys.argv[1]
changed = []
for f in glob.glob('/home/ard/los17/vendor/lenovo/a1000/*.mk') + \
         glob.glob('/home/ard/los17/device/lenovo/a1000/*.mk'):
    lines = io.open(f, encoding='utf-8').read().split('\n')
    def is_dup(l):
        return 'proprietary/' in l and l.rstrip().rstrip(BS).rstrip().endswith(':' + dest)
    out = [l for l in lines if not is_dup(l)]
    if out == lines:
        continue
    # список не должен заканчиваться строкой с косой чертой
    for i, l in enumerate(out):
        if l.rstrip().endswith(BS) and (i + 1 >= len(out) or out[i + 1].strip() == ''):
            out[i] = l.rstrip()[:-1].rstrip()
    io.open(f, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
    changed.append(f.split('/')[-1])
print(('убрано %s из: %s' % (dest, ', '.join(changed))) if changed else ('НЕ НАЙДЕНО: ' + dest))
