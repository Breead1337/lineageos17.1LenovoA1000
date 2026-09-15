/* A1000: проверка гипотезы «слой OSD погашен».
 *
 * Заливает нулевой буфер framebuffer сплошным цветом и делает FBIOPAN_DISPLAY.
 * Пан заводит sprdfb_dispc_refresh(), а тот возвращает dispc_set_osd_alpha(0xff),
 * который sprdfb_dispc_clean_lcd() выставил в 0x00 на инициализации/пробуждении.
 *
 * Если после запуска экран заливается цветом — виновата именно потерянная
 * видимость слоя, и чинить надо в clean_lcd. Если остаётся чёрным — дело не в
 * alpha, а в самом сканировании.
 */
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <linux/fb.h>

int main(int argc, char **argv)
{
    struct fb_var_screeninfo vi;
    struct fb_fix_screeninfo fi;
    unsigned int color = (argc > 1) ? (unsigned int) strtoul(argv[1], 0, 16) : 0xff0000ffu;
    unsigned int *p;
    size_t px, i;
    int fd = open("/dev/graphics/fb0", O_RDWR);

    if (fd < 0) { perror("open fb0"); return 1; }
    if (ioctl(fd, FBIOGET_VSCREENINFO, &vi) || ioctl(fd, FBIOGET_FSCREENINFO, &fi)) {
        perror("ioctl get"); return 1;
    }
    printf("%ux%u vir %ux%u bpp=%u len=%u\n",
           vi.xres, vi.yres, vi.xres_virtual, vi.yres_virtual, vi.bits_per_pixel, fi.smem_len);

    p = mmap(0, fi.smem_len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }

    px = (size_t) vi.xres * vi.yres;
    for (i = 0; i < px; i++) p[i] = color;
    printf("залил %u пикселей цветом %08x\n", (unsigned) px, color);

    vi.yoffset = 0;
    vi.activate = FB_ACTIVATE_VBL;
    if (ioctl(fd, FBIOPAN_DISPLAY, &vi)) perror("FBIOPAN_DISPLAY");
    else printf("FBIOPAN_DISPLAY прошёл\n");
    return 0;
}
