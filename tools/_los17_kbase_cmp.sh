#!/bin/bash
# Сверка нашего ядерного .config с требованиями Android 10 (Q).
# Своего списка под 3.10 у гугла нет (в q/ только 4.4+), берём ближайший — 4.4.
K=/home/ard/a1000-kernel
C=/home/ard/los17/kernel/configs/q
echo "варианты: $(ls $C)"
F=$C/android-4.9/android-base.config
echo "############ $F: чего нет в нашем .config ############"
grep -E '^CONFIG_' $F | while read -r line; do
  sym=${line%%=*}
  grep -qx -- "$line" $K/.config || printf "%-44s у нас: %s\n" "$line" "$(grep -E "^($sym=|# $sym )" $K/.config || echo НЕТ)"
done
echo
echo "############ есть ли эти символы в Kconfig нашего 3.10 ############"
grep -E '^CONFIG_' $F | while read -r line; do
  sym=${line%%=*}; s=${sym#CONFIG_}
  grep -qx -- "$line" $K/.config && continue
  if grep -rqE "^\s*(menu)?config $s\b" $K --include=Kconfig* 2>/dev/null; then echo "ЕСТЬ В KCONFIG: $s"; else echo "нет в ядре 3.10: $s"; fi
done
