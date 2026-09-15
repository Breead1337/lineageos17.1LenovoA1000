# -*- coding: utf-8 -*-
# LOS 17.1 / A1000: экран оффлайн-зарядки не перелистывает кадры.
#
# minui (его статически линкует /system/bin/charger) на каждом Flip() делает
# FBIOPUT_VSCREENINFO с yres_virtual = 2 * height. У sprdfb буферов ТРИ
# (FRAMEBUFFER_NR: virtual_size 480x2400), а sprdfb_check_var отвергает любую
# смену yres_virtual -> EINVAL («active fb swap failed»). yoffset не меняется,
# половина кадров рисуется в невидимый буфер, вторая — прямо в видимый.
# Не трогаем yres_virtual, если буферов и так хватает: тогда меняется только
# yoffset, fb_set_var уходит в sprdfb_pan_display — честное перелистывание.
import io

p = '/home/ard/los17/bootable/recovery/minui/graphics_fbdev.cpp'
s = io.open(p, encoding='utf-8').read()
old = '  vi.yres_virtual = gr_framebuffer[0]->height * 2;\n'
new = ('  // A1000: у sprdfb yres_virtual = 3 кадра и check_var не даёт его менять.\n'
       '  if (vi.yres_virtual < gr_framebuffer[0]->height * 2) {\n'
       '    vi.yres_virtual = gr_framebuffer[0]->height * 2;\n'
       '  }\n')
if 'A1000' in s:
    print('graphics_fbdev.cpp: уже')
else:
    assert s.count(old) == 1
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s.replace(old, new))
    print('graphics_fbdev.cpp: yres_virtual больше не сбрасывается')
