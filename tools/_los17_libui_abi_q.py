# -*- coding: utf-8 -*-
u"""A1000 / Android 10: два символа libui, которых блобу графики не хватает.

ЗАЧЕМ. Из logcat:
    E HAL: load: module=/system/lib/hw/hwcomposer.sc8830.so
    E HAL: dlopen failed: cannot locate symbol "_ZN7android13GraphicBuffer4lockEjPPv"
    I ComposerHal: falling back to gralloc module

Блоб композитора НЕ ГРУЗИТСЯ, и это корень всей истории с пустым экраном:
композитор откатывается на framebuffer HAL, SurfaceFlinger просит буфер с
GRALLOC_USAGE_HW_FB, gralloc отдаёт его ИЗ КАДРОВОГО БУФЕРА, а такой handle не
передаётся через binder (в kmsg: «binder: got transaction with invalid fd, -1»).
SF получает NO_RESOURCES, кадр не собирается, WindowManager блокируется и
Watchdog убивает system_server:
    E GraphicBufferAllocator: Failed to allocate (480 x 800) ... usage 1a00: 5
    W Watchdog: *** WATCHDOG KILLING SYSTEM PROCESS: Blocked in handler on main thread

ВАЖНО: «gralloc0 allocation failed» в логе НЕТ ни разу — сам gralloc отработал.
Пятёрка (NO_RESOURCES) здесь означает развал HIDL-транзакции, а не отказ
gralloc. Это ровно та ловушка, что описана в [[a1000-binder-fd-transfer-fix]].

Сверка UND-символов блоба с собранными библиотеками дала ровно два пробела
(operator new/delete приходят из libc++ и в счёт не идут):

  _ZN7android13GraphicBuffer4lockEjPPv
      В десятке у GraphicBuffer::lock появились выходные параметры
      bytesPerPixel/bytesPerStride, манглинг стал ...lockEjPPvPiS3_.
      Перегрузку добавить нельзя — она будет неоднозначной с версией со
      значениями по умолчанию, поэтому старое имя даём шимом.

  _ZN7android5FenceD1Ev
      В 8.1 деструктор был объявлен как ~Fence(); и символ существовал.
      В десятке он стал = default и встроился. Возвращаем ему тело —
      правка на две строки и без предположений о раскладке класса
      (деструктор приватный, из шима его не позвать).

Оба блоба (gralloc и hwcomposer) линкуют libui_shim.so через DT_NEEDED, так что
шим приезжает вместе с ними и LD_PRELOAD для этого не нужен.
"""
import io

T = '/home/ard/los17/'

# ---------- 1. GraphicBuffer::lock(uint32,void**) — в шим ----------
P = T + 'external/libui_shim/libsprdshim_cpp.cpp'
s = io.open(P, encoding='utf-8').read()
if 'GraphicBuffer4lockEjPPv' in s:
    print(u'libsprdshim_cpp.cpp: GraphicBuffer::lock уже есть')
else:
    anchor = u'/* ===== GraphicBuffer::GraphicBuffer('
    assert anchor in s, u'не найден якорь конструктора GraphicBuffer'
    add = (
        u'/* ===== GraphicBuffer::lock(uint32 usage, void** vaddr) =====\n'
        u' * legacy: _ZN7android13GraphicBuffer4lockEjPPv\n'
        u' * В десятке к lock добавили выходные bytesPerPixel/bytesPerStride, из-за\n'
        u' * чего манглинг стал ...lockEjPPvPiS3_ и старое имя пропало. Блобу\n'
        u' * hwcomposer.sc8830.so нужно именно старое — без него dlopen блоба падает\n'
        u' * и композитор откатывается на framebuffer HAL. */\n'
        u'extern "C" status_t _sprdshim_gb_lock(GraphicBuffer* self,\n'
        u'        uint32_t usage, void** vaddr)\n'
        u'    asm("_ZN7android13GraphicBuffer4lockEjPPv");\n'
        u'extern "C" status_t _sprdshim_gb_lock(GraphicBuffer* self,\n'
        u'        uint32_t usage, void** vaddr) {\n'
        u'    return self->lock(usage, vaddr);\n'
        u'}\n'
        u'\n')
    s = s.replace(anchor, add + anchor, 1)
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'libsprdshim_cpp.cpp: добавлен GraphicBuffer::lock(uint32,void**)')

# ---------- 2. ~Fence() — обратно из inline в отдельный символ ----------
P = T + 'frameworks/native/libs/ui/include/ui/Fence.h'
s = io.open(P, encoding='utf-8').read()
if 'A1000' in s:
    print(u'Fence.h: уже правлен')
else:
    old = u'    ~Fence() = default;'
    assert old in s, u'Fence.h: не найден ~Fence() = default'
    new = (u'    // A1000: в 8.1 деструктор был не встроенным и давал символ\n'
           u'    // _ZN7android5FenceD1Ev, который нужен блобу hwcomposer.sc8830.so.\n'
           u'    // Из шима его не подменить — он приватный. Возвращаем тело в Fence.cpp.\n'
           u'    ~Fence();')
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s.replace(old, new, 1))
    print(u'Fence.h: ~Fence() объявлен без тела')

P = T + 'frameworks/native/libs/ui/Fence.cpp'
s = io.open(P, encoding='utf-8').read()
if 'Fence::~Fence' in s:
    print(u'Fence.cpp: тело деструктора уже есть')
else:
    old = u'namespace android {'
    assert old in s, u'Fence.cpp: не найден namespace android'
    new = (u'namespace android {\n'
           u'\n'
           u'// A1000: см. Fence.h — деструктор нужен отдельным символом.\n'
           u'Fence::~Fence() = default;')
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s.replace(old, new, 1))
    print(u'Fence.cpp: добавлено тело ~Fence()')
