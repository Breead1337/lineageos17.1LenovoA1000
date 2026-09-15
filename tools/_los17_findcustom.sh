#!/bin/bash
# Наши собственные каталоги в дереве 8.1 (не git-проекты манифеста) — их надо перенести.
S=/home/ard/los15.1
T=/home/ard/los17
cd $S
for d in $(find . -mindepth 2 -maxdepth 3 -type d -not -path "./out/*" -not -path "./.repo/*" -not -path "*/.git/*" 2>/dev/null); do
  [ -e "$d/.git" ] || continue
done
# каталоги второго уровня без .git внутри и без .git у родителя
for d in $(ls -d */*/ 2>/dev/null | grep -v "^out/\|^\.repo/"); do
  p=${d%/}
  parent=$(dirname $p)
  [ -e "$p/.git" ] && continue
  [ -e "$parent/.git" ] && continue
  # не покрыт манифестом?
  if [ ! -d "$T/$p" ]; then echo "НЕТ В 17.1: $p"; fi
done
