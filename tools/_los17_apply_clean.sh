#!/bin/bash
# Правки 8.1, которые ложатся на 17.1 без изменений.
P=/home/ard/a1000_81_patches; T=/home/ard/los17
for pair in "packages/apps/FMRadio packages_apps_FMRadio" \
            "external/tinyalsa external_tinyalsa" \
            "packages/inputmethods/LatinIME packages_inputmethods_LatinIME" \
            "external/noto-fonts external_noto-fonts"; do
  set -- $pair; d=$1; f=$P/$2.patch
  cd $T/$d
  if git diff --quiet && git apply "$f" 2>/dev/null; then
    echo "OK   $d"
  else
    if git apply --check "$f" 2>/dev/null; then git apply "$f" && echo "OK   $d"; else echo "ПРОПУСК (уже наложено или конфликт) $d"; fi
  fi
  git diff --stat | tail -2
done
