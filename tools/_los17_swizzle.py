# -*- coding: utf-8 -*-
# LOS 17.1 / A1000: компенсация перестановки каналов панели на Mali + шим вывода.
#
# Панель/DISPC отдаёт кадр с обменянными R и B, компенсация живёт в шейдере GPU.
# Перенос из 8.1: там правился services/surfaceflinger/RenderEngine/ProgramCache,
# в десятке это отдельная библиотека libs/renderengine/gl/ProgramCache.
# Бит ключа берём 13 — первый свободный (последний занятый Y410_BT2020 = 12).
#
# Перестановка нужна ТОЛЬКО при выводе на экран: на время снимка экрана её
# выключаем, иначе screencap и превью в «недавних» выходят с обменянными R и B.
#
# Плюс LD_PRELOAD libui_shim.so в surfaceflinger.rc — тот самый шим вывода кадра
# (external/libui_shim), через который сделана зерокопия и честный vsync.
import io

R = '/home/ard/los17/frameworks/native/'

# ---------- ProgramCache.h: бит ключа ----------
H = R + 'libs/renderengine/gl/ProgramCache.h'
s = io.open(H, encoding='utf-8').read()
if 'SWIZZLE_SHIFT' in s:
    print('ProgramCache.h: уже правлен')
else:
    anchor = """            Y410_BT2020_ON = 1 << Y410_BT2020_SHIFT,"""
    add = anchor + """

            /* A1000: перестановка каналов под панель. Нужна ТОЛЬКО при выводе
             * на экран, в снимок экрана попадать не должна. Бит 13 — первый
             * свободный после Y410_BT2020 (12). */
            SWIZZLE_SHIFT = 13,
            SWIZZLE_MASK = 1 << SWIZZLE_SHIFT,
            SWIZZLE_OFF = 0 << SWIZZLE_SHIFT,
            SWIZZLE_ON = 1 << SWIZZLE_SHIFT,"""
    assert anchor in s, 'не найден конец перечисления Key'
    s = s.replace(anchor, add, 1)

    anchor2 = """        inline bool isY410BT2020() const {"""
    add2 = """        inline bool hasSwizzle() const { return (mKey & SWIZZLE_MASK) == SWIZZLE_ON; }
""" + anchor2
    assert anchor2 in s, 'не найден isY410BT2020'
    s = s.replace(anchor2, add2, 1)
    io.open(H, 'w', encoding='utf-8').write(s)
    print('ProgramCache.h: бит SWIZZLE (13) и hasSwizzle()')

# ---------- ProgramCache.cpp: ключ, переключатель и сам шейдер ----------
C = R + 'libs/renderengine/gl/ProgramCache.cpp'
s = io.open(C, encoding='utf-8').read()
if 'a1000_setSwizzleEnabled' in s:
    print('ProgramCache.cpp: уже правлен')
else:
    if '#include <cutils/properties.h>' not in s:
        s = s.replace('#include <utils/String8.h>',
                      '#include <utils/String8.h>\n#include <cutils/properties.h>', 1)

    old_key = """    needs.set(Key::Y410_BT2020_MASK,
              description.isY410BT2020 ? Key::Y410_BT2020_ON : Key::Y410_BT2020_OFF);"""
    new_key = old_key + """

    // A1000: перестановка каналов идёт в ключ программы, поэтому обе
    // разновидности шейдера спокойно живут в кеше рядом.
    needs.set(Key::SWIZZLE_MASK, a1000_swizzleEnabled() ? Key::SWIZZLE_ON : Key::SWIZZLE_OFF);"""
    assert old_key in s, 'не найден Y410 в computeKey'
    s = s.replace(old_key, new_key, 1)

    # переключатель — до computeKey
    anchor_fn = "ProgramCache::Key ProgramCache::computeKey(const Description& description) {"
    add_fn = """/* A1000: снимок экрана рисуется без перестановки каналов — она компенсирует
 * панель и нужна только на пути вывода. Функция свободная и extern "C", чтобы
 * SurfaceFlinger мог объявить её одной строкой, не таща сюда заголовки GLES. */
static bool gA1000Swizzle = true;
bool a1000_swizzleEnabled() { return gA1000Swizzle; }

""" + anchor_fn
    assert anchor_fn in s, 'не найден computeKey'
    s = s.replace(anchor_fn, add_fn, 1)

    # объявление в начале namespace-блока
    anchor_ns = "namespace gl {"
    assert anchor_ns in s, 'не найден namespace gl'
    s = s.replace(anchor_ns, anchor_ns + "\n\nbool a1000_swizzleEnabled();", 1)

    # сам шейдер
    old_fs = """    fs << dedent << "}";
    return fs.getString();
}

std::unique_ptr<Program> ProgramCache::generateProgram(const Key& needs) {"""
    new_fs = """    // A1000 sc7731: компенсируем перестановку каналов DISPC/GSP/панели на Mali.
    // Настраивается на ходу свойством debug.sf.swz (три буквы rgb, например brg);
    // "rgb" отключает. Значение по умолчанию — brg, как на 8.1 и 9.
    if (needs.hasSwizzle()) {
        char swz[PROPERTY_VALUE_MAX];
        property_get("debug.sf.swz", swz, "brg");
        bool ok = (strlen(swz) == 3);
        for (int i = 0; i < 3 && ok; i++) {
            if (swz[i] != 'r' && swz[i] != 'g' && swz[i] != 'b') ok = false;
        }
        if (!ok) { swz[0] = 'b'; swz[1] = 'r'; swz[2] = 'g'; swz[3] = 0; }
        if (!(swz[0] == 'r' && swz[1] == 'g' && swz[2] == 'b')) {
            String8 line;
            line.appendFormat("gl_FragColor.rgb = gl_FragColor.%s;", swz);
            fs << line;
        }
    }

    fs << dedent << "}";
    return fs.getString();
}

std::unique_ptr<Program> ProgramCache::generateProgram(const Key& needs) {"""
    assert old_fs in s, 'не найден конец generateFragmentShader'
    s = s.replace(old_fs, new_fs, 1)

    # сам переключатель для внешнего мира
    s = s.replace("bool a1000_swizzleEnabled() { return gA1000Swizzle; }",
                  "bool a1000_swizzleEnabled() { return gA1000Swizzle; }\n"
                  "extern \"C\" void a1000_setSwizzleEnabled(bool enabled) { gA1000Swizzle = enabled; }", 1)
    io.open(C, 'w', encoding='utf-8').write(s)
    print('ProgramCache.cpp: шейдер, ключ и переключатель')

# ---------- SurfaceFlinger.cpp: снимок экрана без перестановки ----------
F = R + 'services/surfaceflinger/SurfaceFlinger.cpp'
s = io.open(F, encoding='utf-8').read()
if 'a1000_setSwizzleEnabled' in s:
    print('SurfaceFlinger.cpp: уже правлен')
else:
    # объявление обязано быть на уровне файла: C++ не разрешает
    # спецификацию связывания extern "C" внутри блока.
    old = """void SurfaceFlinger::renderScreenImplLocked(const RenderArea& renderArea,
                                            TraverseLayersFunction traverseLayers,
                                            ANativeWindowBuffer* buffer, bool useIdentityTransform,
                                            int* outSyncFd) {
    ATRACE_CALL();"""
    new = """/* A1000: определена в renderengine/gl/ProgramCache.cpp; объявляем здесь,
 * чтобы не тащить в SurfaceFlinger заголовки GLES. */
extern "C" void a1000_setSwizzleEnabled(bool enabled);

void SurfaceFlinger::renderScreenImplLocked(const RenderArea& renderArea,
                                            TraverseLayersFunction traverseLayers,
                                            ANativeWindowBuffer* buffer, bool useIdentityTransform,
                                            int* outSyncFd) {
    /* A1000: снимок экрана рисуем БЕЗ перестановки каналов — она компенсирует
     * панель и нужна только на пути вывода. Иначе screencap и превью в
     * «недавних» получаются с обменянными красным и синим. */
    class SwizzleOff {
    public:
        SwizzleOff() { a1000_setSwizzleEnabled(false); }
        ~SwizzleOff() { a1000_setSwizzleEnabled(true); }
    } a1000SwizzleOff;

    ATRACE_CALL();"""
    assert old in s, 'не найден renderScreenImplLocked'
    s = s.replace(old, new, 1)
    io.open(F, 'w', encoding='utf-8').write(s)
    print('SurfaceFlinger.cpp: снимок экрана без перестановки')

# ---------- surfaceflinger.rc: шим вывода ----------
RC = R + 'services/surfaceflinger/surfaceflinger.rc'
s = io.open(RC, encoding='utf-8').read()
if 'libui_shim' in s:
    print('surfaceflinger.rc: уже правлен')
else:
    old = "    group graphics drmrpc readproc"
    new = old + "\n    setenv LD_PRELOAD libui_shim.so"
    assert old in s, 'не найдена строка group в surfaceflinger.rc'
    s = s.replace(old, new, 1)
    io.open(RC, 'w', encoding='utf-8').write(s)
    print('surfaceflinger.rc: LD_PRELOAD libui_shim.so')
