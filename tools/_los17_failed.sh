#!/bin/bash
# Какие проекты не докачались в последней попытке.
L=/home/ard/los17_sync.log
START=$(grep -n "попытка" $L | tail -2 | head -1 | cut -d: -f1)
echo "=== ошибки последней завершённой попытки ==="
sed -n "${START},\$p" $L | grep -oP "on \K[^ ]+(?= failed)" | sort -u
echo "=== всего проектов не выложено ==="
cd /home/ard/los17
python3 - <<'PY'
import subprocess, os, re, xml.etree.ElementTree as ET
base='/home/ard/los17'
paths=set()
for f in ['.repo/manifests/default.xml']+[os.path.join('.repo/manifests/snippets',x) for x in os.listdir(base+'/.repo/manifests/snippets')]:
    try: t=ET.parse(os.path.join(base,f))
    except Exception: continue
    for p in t.getroot().iter('project'):
        paths.add(p.get('path') or p.get('name'))
missing=[p for p in sorted(paths) if not os.path.isdir(os.path.join(base,p)) or not os.listdir(os.path.join(base,p))]
print('пусто/нет:', len(missing), 'из', len(paths))
for m in missing[:40]: print('   ', m)
PY
