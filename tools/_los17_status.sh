#!/bin/bash
M=/home/ard/los17
cd $M
echo "занято: $(df -h $M | tail -1 | awk '{print $3}')  .repo: $(du -sh .repo 2>/dev/null | cut -f1)"
echo "проектов в манифесте: $(grep -ch '<project' .repo/manifests/default.xml .repo/manifests/snippets/*.xml 2>/dev/null | paste -sd+ | bc)"
echo "склонировано: $(find .repo/projects -maxdepth 8 -name '*.git' -type d 2>/dev/null | wc -l)"
echo "верхнеуровневых каталогов дерева: $(ls -A $M | wc -l)"
echo "ключевые репозитории:"
for d in build/make frameworks/base frameworks/native system/core system/sepolicy hardware/interfaces vendor/lineage kernel/configs external/tinyalsa; do
  if [ -d "$M/$d" ]; then printf "  %-24s %s\n" "$d" "$(ls -A $M/$d | wc -l) файлов"; else printf "  %-24s ЕЩЁ НЕТ\n" "$d"; fi
done
pgrep -f _los17_sync >/dev/null && echo "СИНК ИДЁТ" || echo "СИНК НЕ РАБОТАЕТ"
tail -2 /home/ard/los17_sync.log
