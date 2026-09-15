#!/bin/bash
# Автоцикл: гоняем kati и на каждое «overriding commands for target» выкидываем
# КОПИРОВАНИЕ блоба, оставляя модуль из исходников. Так можно, потому что
# коллизия возникает только с ОБЩИМИ модулями AOSP: железозависимые блобы
# sc8830 из исходников не собираются и в конфликт не вступают.
# Лог: /home/ard/los17_dup.log
F=/mnt/c/Users/Stanislav/Desktop/NPU/firmware
L=/home/ard/los17_dup.log
: > $L
rm -f /home/ard/los17_dup.finished
for i in $(seq 1 20); do
  echo "=== проход $i ===" >> $L
  bash $F/_los17.sh 'mka nothing -j10' > /tmp/dup_out.txt 2>&1
  D=$(grep -oP "overriding commands for target .out/target/product/a1000/\K[^']+" /tmp/dup_out.txt | head -1)
  if [ -z "$D" ]; then
    echo "дублей больше нет (проход $i)" >> $L
    tail -6 /tmp/dup_out.txt >> $L
    break
  fi
  echo "дубль: $D" >> $L
  python3 $F/_los17_dupdel.py "$D" > /tmp/dupdel.txt 2>&1
  cat /tmp/dupdel.txt >> $L
  if grep -q "НЕ НАЙДЕНО" /tmp/dupdel.txt; then
    echo "не смог убрать сам — нужна ручная правка, выхожу" >> $L
    break
  fi
done
echo "=== ИТОГ ===" >> $L
grep "^дубль" $L >> $L
echo done > /home/ard/los17_dup.finished
