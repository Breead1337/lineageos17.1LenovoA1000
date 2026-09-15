# -*- coding: utf-8 -*-
u"""A1000 / Android 10: объявление a1000_setSwizzleEnabled — на уровне файла.

_los17_swizzle.py клал `extern "C" void a1000_setSwizzleEnabled(bool);` внутрь
renderScreenImplLocked, а C++ не разрешает спецификацию связывания в блоке:
    SurfaceFlinger.cpp:6032:12: error: expected unqualified-id
Здесь чиним уже пропатченное дерево; сам _los17_swizzle.py тоже поправлен, так
что повторный прогон порта поломку не вернёт.
"""
import io

DECL = u'    extern "C" void a1000_setSwizzleEnabled(bool enabled);  /* renderengine/gl/ProgramCache.cpp */\n'
ANCHOR = u'void SurfaceFlinger::renderScreenImplLocked(const RenderArea& renderArea,'
FILE_DECL = (u'/* A1000: определена в renderengine/gl/ProgramCache.cpp; объявляем здесь,\n'
             u' * чтобы не тащить в SurfaceFlinger заголовки GLES. */\n'
             u'extern "C" void a1000_setSwizzleEnabled(bool enabled);\n\n')

P = '/home/ard/los17/frameworks/native/services/surfaceflinger/SurfaceFlinger.cpp'
s = io.open(P, encoding='utf-8').read()
if FILE_DECL in s:
    print(u'SurfaceFlinger.cpp: уже правлен')
else:
    assert DECL in s, u'объявления внутри функции нет'
    assert ANCHOR in s, u'не найдено определение renderScreenImplLocked'
    s = s.replace(DECL, u'', 1).replace(ANCHOR, FILE_DECL + ANCHOR, 1)
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print(u'SurfaceFlinger.cpp: объявление вынесено на уровень файла')
