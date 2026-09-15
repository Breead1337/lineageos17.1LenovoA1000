# -*- coding: utf-8 -*-
u"""A1000 / Android 10: не пускать GRALLOC_USAGE_HW_FB в старый gralloc.

ЗАЧЕМ. После того как блоб композитора наконец загрузился (см.
_los17_libui_abi_q.py), экран всё равно пустой, и в логе бесконечно:
    E GraphicBufferAllocator: Failed to allocate (480 x 800) layerCount 1 format 1 usage 1a00: 5
    E BufferQueueProducer: [FramebufferSurface] dequeueBuffer: createGraphicBuffer failed
    E CompositionEngine: ANativeWindow::dequeueBuffer failed ... error: -12
    W Watchdog: *** WATCHDOG KILLING SYSTEM PROCESS: Blocked in handler on main thread

usage 0x1a00 = HW_FB | HW_COMPOSER | HW_RENDER — это FramebufferSurface, у
которого набор бит зашит в конструкторе SurfaceFlinger.

Строки «gralloc0 allocation failed» в логе НЕТ ни разу: сам gralloc отработал.
Пятёрка — это NO_RESOURCES, которым Gralloc2Allocator одинаково отвечает и на
отказ gralloc, и на РАЗВАЛ HIDL-ТРАНЗАКЦИИ (kTransactionError). Разваливается
именно транзакция, и kmsg говорит чем:
    binder: 217:250 got transaction with invalid fd, -1
    binder: send failed reply for transaction 1387 to 232:232

Причина. На GRALLOC_USAGE_HW_FB старый gralloc уходит в
gralloc_alloc_framebuffer: отображает кадровый буфер (в логе видно
«[Gralloc]: using (fd=7)», xres/yres/bpp) и отдаёт буфер ИЗ НЕГО. У такого
handle нет передаваемого дескриптора — только адрес и смещение внутри чужого
процесса. Аллокатор в десятке отдельный процесс, дескриптор -1 едет через
binder и транзакция гибнет.

На 8.1 этого не было: там HW_FB до gralloc не доезжал, и FB-таргет был обычным
буфером ION — ровно так и написано в шапке
external/libui_shim/libsprdshim_fbpost.cpp («Наш FB-таргет — обычный ION (HW_FB
в Android 8.1 не поддерживается gralloc1on0)»). Вся зерокопия построена именно
на этом: a1000_overlay_post получает ION-буфер и направляет на него DISPC.

ВАЖНО, где править. На этом устройстве живёт НЕ gralloc1-adapter — статическая
библиотека libgralloc1-adapter в сборку вообще не входит, на неё никто не
ссылается. Живой путь прямой: allocator@2.0-impl (passthrough) ->
Gralloc0HalImpl::allocateOneBuffer -> mDevice->alloc.
"""
import io

P = ('/home/ard/los17/hardware/interfaces/graphics/allocator/2.0/utils/'
     'passthrough/include/allocator-passthrough/2.0/Gralloc0Hal.h')
s = io.open(P, encoding='utf-8').read()

if 'A1000: HW_FB' in s:
    print(u'Gralloc0Hal.h: уже правлен')
else:
    old = (
        "        const native_handle_t* buffer = nullptr;\n"
        "        int stride = 0;\n"
        "        int result = mDevice->alloc(mDevice, info.width, info.height, static_cast<int>(info.format),\n"
        "                                    info.usage, &buffer, &stride);\n")
    assert old in s, u'не найден вызов mDevice->alloc'
    new = (
        "        const native_handle_t* buffer = nullptr;\n"
        "        int stride = 0;\n"
        "        // A1000: HW_FB уводит старый gralloc в gralloc_alloc_framebuffer, и он\n"
        "        // отдаёт буфер ИЗ кадрового буфера. У такого handle нет передаваемого\n"
        "        // дескриптора (в kmsg: binder: got transaction with invalid fd, -1),\n"
        "        // а аллокатор здесь — отдельный процесс, поэтому HIDL-транзакция\n"
        "        // разваливается и SurfaceFlinger получает NO_RESOURCES на каждый кадр.\n"
        "        // В 8.1 этот бит до gralloc не доходил и FB-таргет был обычным ION —\n"
        "        // на этом построена зерокопия (libsprdshim_fbpost.cpp). Возвращаем то же.\n"
        "        uint64_t a1000Usage = info.usage & ~uint64_t(GRALLOC_USAGE_HW_FB);\n"
        "        int result = mDevice->alloc(mDevice, info.width, info.height, static_cast<int>(info.format),\n"
        "                                    a1000Usage, &buffer, &stride);\n")
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'Gralloc0Hal.h: HW_FB снимается перед вызовом gralloc0')
