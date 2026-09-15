# -*- coding: utf-8 -*-
import io
p = '/home/ard/los17/device/lenovo/a1000/rootdir/bin/a1000_logs.sh'
s = io.open(p, encoding='utf-8').read()
if 'kstream' in s:
    print('уже'); raise SystemExit
pairs = [
(u'''for f in uboot kmsg kmsg_boot logcat logcat_boot props; do
    rm -f $LOGDIR/$f.prev.txt
    [ -f $LOGDIR/$f.txt ] && mv -f $LOGDIR/$f.txt $LOGDIR/$f.prev.txt
done
rm -f $LOGDIR/logcat.txt.1 $LOGDIR/logcat.txt.2 $LOGDIR/logcat.txt.3
''',
u'''for f in uboot kmsg kmsg_boot kstream logcat logcat_boot props; do
    rm -f $LOGDIR/$f.prev.txt
    [ -f $LOGDIR/$f.txt ] && mv -f $LOGDIR/$f.txt $LOGDIR/$f.prev.txt
done
# хвосты ротации logcat прошлой загрузки тоже сохраняем (раньше удалялись)
for n in 1 2 3; do
    rm -f $LOGDIR/logcat.prev.txt.$n
    [ -f $LOGDIR/logcat.txt.$n ] && mv -f $LOGDIR/logcat.txt.$n $LOGDIR/logcat.prev.txt.$n
done
'''),
(u'''logcat -b all -v threadtime -f $LOGDIR/logcat.txt -r 4096 -n 3 &
''',
u'''logcat -b all -v threadtime -f $LOGDIR/logcat.txt -r 4096 -n 3 &

# --- 4a. Поток ядра ---------------------------------------------------------
# Снимок dmesg раз в 20 с не успевал к моменту зависания (14.09: хвост терялся
# вместе с page cache). Поток dmesg -w + sync каждые 3 с — теряем максимум 3 с.
dmesg -w > $LOGDIR/kstream.txt 2>/dev/null &
'''),
(u'''while true; do
    dmesg > $LOGDIR/kmsg.txt 2>/dev/null
''',
u'''i=0
while true; do
    sync
    sleep 3
    i=$((i + 1))
    [ $((i % 7)) = 0 ] || continue

    dmesg > $LOGDIR/kmsg.txt 2>/dev/null
'''),
(u'''    chmod -R 0666 $LOGDIR/*.txt 2>/dev/null
    sleep $DMESG_PERIOD
done''',
u'''    chmod -R 0666 $LOGDIR/*.txt* 2>/dev/null
done'''),
(u'''               rm -f $LOGDIR/logcat.txt.3 $LOGDIR/logcat.txt.2
''',
u'''               rm -f $LOGDIR/logcat.txt.3 $LOGDIR/logcat.txt.2 $LOGDIR/logcat.prev.txt.*
'''),
]
for old, new in pairs:
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)
s = s.replace(u'DMESG_PERIOD=20          # как часто перезаписывать снимок кольцевого буфера ядра\n', u'')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('a1000_logs.sh: правлен')
