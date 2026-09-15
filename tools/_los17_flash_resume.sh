#!/bin/bash
# Заливка system кусками с автоподхватом после обрыва USB.
#
# Куски независимы: каждый пишется в свою позицию раздела через dd seek, повтор
# безопасен. USB на этом кабеле рвётся раз в несколько кусков, поэтому крутим
# _los16_flash_chunks.sh, каждый раз продолжая с первого незаписанного.
#
# ДВЕ грабли, на которых уже наступали:
#  * grep в Git Bash собран БЕЗ -P, поэтому номер куска достаём через sed;
#    молчаливый провал давал N=0, а вызов с нулём ОБНУЛЯЕТ лог прогресса и
#    заливка начиналась заново;
#  * два одновременных заливщика пишут в один и тот же /tmp/chunk.bin на
#    аппарате — один может записать чужой кусок не туда. Держим ровно один.
cd /c/Users/Stanislav/Desktop/NPU/firmware || exit 1
LOG=_flash_progress.txt
A="/c/Users/Stanislav/Desktop/platform-tools/adb.exe"

if pgrep -f _los16_flash_chunks.sh >/dev/null 2>&1; then
  echo "уже идёт другая заливка — выхожу"; exit 1
fi

N=${1:-0}
for i in $(seq 1 30); do
  if grep -q "ГОТОВО" $LOG 2>/dev/null; then echo "ЗАЛИТО"; break; fi
  DONE=$(sed -n 's#^\([0-9][0-9]*\)/15 .*записан#\1#p' $LOG 2>/dev/null | tail -1)
  # номер в логе — сколько кусков записано, значит продолжать с него же
  if [ -n "$DONE" ] && [ "$DONE" -gt "$N" ]; then N=$DONE; fi
  echo "--- заход $i, продолжаем с куска $N ---"
  MSYS_NO_PATHCONV=1 "$A" kill-server >/dev/null 2>&1
  MSYS_NO_PATHCONV=1 "$A" shell "rm -f /tmp/chunk.bin" >/dev/null 2>&1
  bash _los16_flash_chunks.sh $N
done
tail -3 $LOG
