# -*- coding: utf-8 -*-
# LOS 17.1 / A1000: проблемные слои композируем на GPU, а не в вендорном оверлее.
#
# Перенос правки из 8.1 (Layer::setGeometry + layer.setSkip) и из девятки
# (BufferLayer::setPerFrameData + Composition::Client). В десятке место то же,
# что в девятке, поменялась только сигнатура: тип задаётся
# setCompositionType(displayDevice, Hwc2::IComposerClient::Composition::CLIENT).
#
# Почему эти четыре имени (всё проверено живьём на 8.1/9):
#   * ImageWallpaper — побывав в оверлее, портится НЕОБРАТИМО (рисуется один раз);
#   * BootAnimation — на старте единственный слой, уходил в GSP → мерцал фиолетовым;
#   * camera — превью единственный полноэкранный слой, блоб не перечитывал буфер;
#   * StatusBar — со своими обоями блокировки окно keyguard остаётся единственным
#     слоем (см. _los16_keyguard_gles.py, на 8.1 закрыто отдельным zip'ом);
#   * не-RGB (YUV) — блоб гонит через GSP, а тот переставляет R и B.
# Единственный слой = единственный случай, когда блоб вообще берёт оверлей:
# при двух и более он и сам отдаёт всё в Client (замерено на девятке).
#
# debug.sf.force_gles=0 возвращает штатное поведение с оверлеем.
import io

P = '/home/ard/los17/frameworks/native/services/surfaceflinger/BufferLayer.cpp'
s = io.open(P, encoding='utf-8').read()

if 'a1000ForceClient' in s:
    print('BufferLayer.cpp: уже правлен')
    raise SystemExit(0)

old = """    // Device or Cursor layers
    if (mPotentialCursor) {
        ALOGV("[%s] Requesting Cursor composition", mName.string());
        setCompositionType(displayDevice, Hwc2::IComposerClient::Composition::CURSOR);
    } else {
        ALOGV("[%s] Requesting Device composition", mName.string());
        setCompositionType(displayDevice, Hwc2::IComposerClient::Composition::DEVICE);
    }"""

new = """    // A1000: решаем, отдавать ли слой аппаратному оверлею.
    // Подробности и история — в firmware/_los17_force_client.py.
    bool a1000ForceClient = false;
    {
        char fg[PROPERTY_VALUE_MAX];
        property_get("debug.sf.force_gles", fg, "1");
        a1000ForceClient = (fg[0] != '0');

        const char* name = mName.string();
        // Обои: один раз побывав в оверлее, портятся необратимо.
        if (!a1000ForceClient && strstr(name, "ImageWallpaper") != NULL) {
            a1000ForceClient = true;
        }
        // Бут-анимация: единственный слой на старте, GSP переставляет R и B.
        if (!a1000ForceClient && strstr(name, "BootAnimation") != NULL) {
            a1000ForceClient = true;
        }
        // Камера: превью застывало, буфер блобом не перечитывался.
        if (!a1000ForceClient && strcasestr(name, "camera") != NULL) {
            a1000ForceClient = true;
        }
        // Экран блокировки: со своими обоями окно StatusBar остаётся
        // единственным слоем и в оверлее выводится неверно.
        if (!a1000ForceClient && strstr(name, "StatusBar") != NULL) {
            a1000ForceClient = true;
        }
        // YUV и прочее не-RGB блоб гонит через GSP — те же переставленные
        // каналы и застывший кадр.
        if (!a1000ForceClient && mActiveBuffer != nullptr) {
            switch (mActiveBuffer->getPixelFormat()) {
                case HAL_PIXEL_FORMAT_RGBA_8888:
                case HAL_PIXEL_FORMAT_RGBX_8888:
                case HAL_PIXEL_FORMAT_RGB_888:
                case HAL_PIXEL_FORMAT_RGB_565:
                case HAL_PIXEL_FORMAT_BGRA_8888:
                    break;                  // обычные окна — оверлей разрешён
                default:
                    a1000ForceClient = true;
                    break;
            }
        }
    }

    // Device or Cursor layers
    if (a1000ForceClient) {
        ALOGV("[%s] A1000: композиция на GPU", mName.string());
        setCompositionType(displayDevice, Hwc2::IComposerClient::Composition::CLIENT);
    } else if (mPotentialCursor) {
        ALOGV("[%s] Requesting Cursor composition", mName.string());
        setCompositionType(displayDevice, Hwc2::IComposerClient::Composition::CURSOR);
    } else {
        ALOGV("[%s] Requesting Device composition", mName.string());
        setCompositionType(displayDevice, Hwc2::IComposerClient::Composition::DEVICE);
    }"""

assert old in s, 'не найден выбор типа композиции в BufferLayer.cpp'
s = s.replace(old, new, 1)

if '#include <strings.h>' not in s:
    s = s.replace('#include <cutils/properties.h>',
                  '#include <cutils/properties.h>\n#include <string.h>\n#include <strings.h>', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('BufferLayer.cpp: обои, бут-анимация, камера, keyguard и YUV идут на GPU')
