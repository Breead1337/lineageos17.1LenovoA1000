# -*- coding: utf-8 -*-
# LOS 17.1 / A1000: две правки в system/core (перенос из 8.1).
#
# 1) healthd_draw: sprdfb не реализует fb_blank, FBIOBLANK возвращает -EINVAL,
#    поэтому в режиме зарядки подсветка не гасла и жгла ток всю ночь. Гасим
#    свет напрямую через backlight-класс.
# 2) init/selinux.cpp: на этапе подъёма порта не роняем загрузку, если политика
#    не грузится или setenforce не проходит — иначе телефон уходит в фастбут и
#    посмотреть logcat нельзя. В десятке это LOG(FATAL) вместо panic()/
#    security_failure() из восьмёрки.
import io

# ---------- 1. подсветка в режиме зарядки ----------
P = '/home/ard/los17/system/core/healthd/healthd_draw.cpp'
s = io.open(P, encoding='utf-8').read()
if 'set_backlight_power' in s:
    print('healthd_draw.cpp: уже правлен')
else:
    if '#include <fcntl.h>' not in s:
        s = s.replace('#include <cutils/klog.h>',
                      '#include <cutils/klog.h>\n\n#include <fcntl.h>\n#include <unistd.h>', 1)
    old = """void HealthdDraw::blank_screen(bool blank) {
    if (!graphics_available) return;
    gr_fb_blank(blank);
}"""
    new = """// A1000 (и вообще sprdfb): драйвер не реализует fb_blank, поэтому FBIOBLANK
// возвращает -EINVAL и gr_fb_blank() не гасит ровным счётом ничего — в режиме
// зарядки подсветка горела бы всю ночь и съедала весь ток зарядника. Гасим
// свет напрямую через backlight-класс; на устройствах без этого узла open()
// не удастся и поведение останется прежним.
static void set_backlight_power(bool on) {
    int fd = open("/sys/class/backlight/sprd_backlight/bl_power", O_WRONLY | O_CLOEXEC);
    if (fd < 0) return;
    // 0 = FB_BLANK_UNBLANK, 4 = FB_BLANK_POWERDOWN
    TEMP_FAILURE_RETRY(write(fd, on ? "0" : "4", 1));
    close(fd);
}

void HealthdDraw::blank_screen(bool blank) {
    if (!graphics_available) return;
    gr_fb_blank(blank);
    set_backlight_power(!blank);
}"""
    assert old in s, 'не найден blank_screen'
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('healthd_draw.cpp: подсветка гасится напрямую')

# ---------- 2. init не падает из-за SELinux ----------
P = '/home/ard/los17/system/core/init/selinux.cpp'
s = io.open(P, encoding='utf-8').read()
if 'A1000:' in s:
    print('init/selinux.cpp: уже правлен')
else:
    old = """    LOG(INFO) << "Loading SELinux policy";
    if (!LoadPolicy()) {
        LOG(FATAL) << "Unable to load SELinux policy";
    }"""
    new = """    LOG(INFO) << "Loading SELinux policy";
    if (!LoadPolicy()) {
        // A1000: не роняем загрузку — без политики система поднимется в
        // permissive, и будет виден logcat. С LOG(FATAL) телефон уезжает в
        // фастбут и причину не увидеть.
        LOG(ERROR) << "A1000: не удалось загрузить политику SELinux — продолжаем без неё";
        setenv("INIT_SELINUX_TOOK", std::to_string(t.duration().count()).c_str(), 1);
        return;
    }"""
    assert old in s, 'не найден LoadPolicy'
    s = s.replace(old, new, 1)

    old2 = """        if (security_setenforce(is_enforcing)) {
            PLOG(FATAL) << "security_setenforce(%s) failed" << (is_enforcing ? "true" : "false");
        }"""
    new2 = """        if (security_setenforce(is_enforcing)) {
            PLOG(ERROR) << "A1000: security_setenforce failed -> продолжаем";
        }"""
    assert old2 in s, 'не найден setenforce'
    s = s.replace(old2, new2, 1)

    old3 = """    if (auto result = WriteFile("/sys/fs/selinux/checkreqprot", "0"); !result) {
        LOG(FATAL) << "Unable to write to /sys/fs/selinux/checkreqprot: " << result.error();
    }"""
    new3 = """    if (auto result = WriteFile("/sys/fs/selinux/checkreqprot", "0"); !result) {
        LOG(ERROR) << "A1000: checkreqprot не записался: " << result.error();
    }"""
    assert old3 in s, 'не найден checkreqprot'
    s = s.replace(old3, new3, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('init/selinux.cpp: загрузка не падает из-за SELinux')
