#!/usr/bin/env python3
# Ядро: маска ION ~0 («любая куча») -> сначала системная куча.
#
# Codec2 (C2AllocatorIon, маска ~0) и прочие общие клиенты libion SPRD-кучи не
# знают. plist обходит кучи с большего id: ~0 попадала в carveout_overlay (id 3),
# а carveout отдаёт буфер в юзерспейс как strongly-ordered (pgprot_noncached) ->
# невыровненный ldr = SIGBUS BUS_ADRALN в mediaswcodec (C2SoftVorbisDec: OGG,
# звуки UI, затвор камеры) + codec ест память экрана. Откат на полную маску есть.
p = "/home/ard/a1000-kernel/drivers/gpu/ion/ion.c"
s = open(p).read()
old = """			a1000_fallback = 1;
		}
"""
new = """			a1000_fallback = 1;
		} else if (heap_id_mask == ~0u) {
			/* generic "any heap" (Codec2, libion): carveouts are
			 * mapped strongly-ordered -> unaligned SIGBUS */
			heap_id_mask = (1u << 1);   /* ion_heap_system */
			a1000_fallback = 1;
		}
"""
if "generic \"any heap\"" not in s:
    assert s.count(old) == 1
    open(p, "w").write(s.replace(old, new))
    print("ion.c: patched")
else:
    print("ion.c: already patched")
