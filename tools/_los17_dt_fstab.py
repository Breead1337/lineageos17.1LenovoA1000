# -*- coding: utf-8 -*-
u"""A1000 / Android 10: вписать fstab в дерево устройств.

Лог упавшей загрузки (ramoops) сказал ровно это:
    init: init first stage started!
    init: [libfs_mgr]ReadFstabFromDt(): failed to read fstab from dt
    init: First stage mount skipped (missing/incompatible/empty fstab in device tree)
    init: execv("/system/bin/init") failed: No such file or directory

В десятке первая стадия init берёт fstab ТОЛЬКО из дерева устройств
(system/core/fs_mgr/fs_mgr_fstab.cpp: ищет <android-dt>/fstab/compatible ==
"android,fstab"). Отката на файл /fstab.${ro.hardware} в ramdisk нет — он
появится только в одиннадцатой. Не найдя узла, init МОЛЧА пропускает
монтирование, раздел system не поднят, и запускать /system/bin/init неоткуда.

Файл device/lenovo/a1000/prebuilt/sprd.dtb — не голый dtb, а таблица
Spreadtrum: магия SPRD, заголовок 2048 байт (платформа 0x227e = 8830,
смещение и размер блоба), затем сам dtb. Пересобираем блоб и правим размер в
заголовке.
"""
import io, os, struct, subprocess, sys

T = '/home/ard/los17'
SRC = T + '/device/lenovo/a1000/prebuilt/sprd.dtb'
DTC = '/home/ard/a1000-kernel/scripts/dtc/dtc'
OFF_SIZE = 28  # поле «размер блоба» в заголовке SPRD

NODE = u'''
	firmware {
		android {
			compatible = "android,firmware";

			fstab {
				compatible = "android,fstab";

				system {
					compatible = "android,system";
					dev = "/dev/block/platform/sdio_emmc/by-name/system";
					type = "ext4";
					mnt_flags = "ro,barrier=1";
					fsmgr_flags = "wait";
				};
			};
		};
	};
'''

raw = open(SRC, 'rb').read()
assert raw[:4] == b'SPRD', u'не таблица SPRD'
pos = raw.find(b'\xd0\x0d\xfe\xed')
size = struct.unpack('>I', raw[pos + 4:pos + 8])[0]
head, tail = raw[:pos], raw[pos + size:]
open('/tmp/dt_in.dtb', 'wb').write(raw[pos:pos + size])
print(u'блоб: смещение %d, размер %d, хвост %d байт' % (pos, size, len(tail)))

subprocess.check_call([DTC, '-I', 'dtb', '-O', 'dts', '-o', '/tmp/dt.dts', '/tmp/dt_in.dtb'],
                      stderr=subprocess.STDOUT)
dts = io.open('/tmp/dt.dts', encoding='utf-8').read()

if 'android,fstab' in dts:
    print(u'узел fstab уже есть, ничего не делаю')
    sys.exit(0)

cut = dts.rstrip().rfind('\n};')          # закрывающая скобка корневого узла
assert cut > 0, u'не найден конец корневого узла'
dts = dts[:cut] + '\n' + NODE + dts[cut:]
io.open('/tmp/dt_out.dts', 'w', encoding='utf-8', newline='\n').write(dts)

subprocess.check_call([DTC, '-I', 'dts', '-O', 'dtb', '-o', '/tmp/dt_out.dtb', '/tmp/dt_out.dts'],
                      stderr=subprocess.STDOUT)
new = open('/tmp/dt_out.dtb', 'rb').read()
print(u'новый блоб: %d байт (было %d)' % (len(new), size))

pad = (-len(new)) % 4
out = bytearray(head + new + b'\x00' * pad + tail)
struct.pack_into('<I', out, OFF_SIZE, len(new) + pad)

open(SRC, 'wb').write(bytes(out))
print(u'sprd.dtb пересобран, размер файла %d' % len(out))
