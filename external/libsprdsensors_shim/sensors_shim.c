/*
 * libsprdsensors_shim — единственный символ, которого не хватает
 * /system/lib/hw/sensors.sc8830.so на Android 8.1.
 *
 * android_atomic_release_cas() экспортировался libcutils до Android 8, потом его
 * сделали inline и из библиотеки убрали. Блоб слинкован против старой libcutils,
 * поэтому dlopen падает с
 *     cannot locate symbol "android_atomic_release_cas"
 *     Couldn't load sensors module (Unknown error -2147483648)
 * и SensorService зависает, из-за чего загрузка встаёт на бут-анимации.
 *
 * Семантика оригинала (system/core/include/cutils/atomic.h):
 *   int android_atomic_release_cas(int32_t oldvalue, int32_t newvalue,
 *                                  volatile int32_t *addr);
 *   если *addr == oldvalue -> записать newvalue и вернуть 0, иначе вернуть != 0.
 *   Барьер: release при успехе.
 */
#include <stdint.h>

int android_atomic_release_cas(int32_t oldvalue, int32_t newvalue,
                               volatile int32_t *addr)
{
    int32_t expected = oldvalue;
    return __atomic_compare_exchange_n((int32_t *)addr, &expected, newvalue,
                                       0 /* strong */,
                                       __ATOMIC_RELEASE,
                                       __ATOMIC_RELAXED) ? 0 : 1;
}
