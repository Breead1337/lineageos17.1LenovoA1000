# Ядро 3.10 (SC8830) под Android 10

Здесь **только дельта** — файлы, отличающиеся от базы. База:
<https://github.com/Breead1337/lenovoa1000kernel3.10sourceENHANCED>, коммит `e51ce694`.

```sh
git clone https://github.com/Breead1337/lenovoa1000kernel3.10sourceENHANCED a1000-kernel
cp -a kernel/sc8830/. a1000-kernel/       # файлы отсюда кладутся поверх
cd a1000-kernel && ./kbuild_a10_inner.sh  # см. kernel/scripts/
```

Итог — ядро **#106**, оно же лежит собранным в `device/lenovo/a1000/prebuilt/kernel`.

## Что в дельте (26 файлов)

| файл | зачем |
|---|---|
| `arch/arm/configs/a1000_baton4iks_defconfig` | конфиг десятки: требования `android-base.config` для Q, которые 3.10 умеет (XT_MATCH_OWNER, QUOTA, TASKSTATS, IKCONFIG, CRYPTO_GCM/SHA512 и др.) |
| `arch/arm/{include/asm,include/uapi/asm}/unistd.h`, `arch/arm/kernel/calls.S`, `include/linux/syscalls.h`, `include/uapi/linux/memfd.h`, `mm/shmem.c` | системный вызов `memfd_create` — без него не стартует zygote |
| `include/linux/cred.h`, `include/uapi/linux/prctl.h`, `kernel/cred.c`, `kernel/sys.c`, `security/commoncap.c` | ambient capabilities — иначе init падает на первом же сервисе с `capabilities` |
| `drivers/gpu/ion/ion.c` | выделение из любой кучи ION: Codec2 попадал в carveout и OGG не игрались |
| `kernel/cpuset.c` | cpusets для десятки |
| `drivers/regulator/sc2713s-regulator_dt.c` | vddarm (ядро #115) |
| `drivers/video/sprdfb/sprdfb_{dispc,main,panel}.c` | page flip, зеркало, панель |
| `drivers/power/{fan5405.c,sprd_2713_charge.c}` | зарядка |
| `drivers/misc/{Kconfig,Makefile}`, `drivers/misc/uid_cputime.c` | `uid_cputime` — статистика батареи по приложениям |
| `arch/arm/mach-sc/ontim_device.c`, `drivers/ontim/touchscreen/.../mstar_drv_self_fw_control.c` | тач |
| `net/ipv4/fib_semantics.c` | маршрутизация |

Правки накладывались поверх наработок 8.1/9 в общем дереве ядра, поэтому часть
из них (sprdfb, зарядка, тач) относится не только к десятке.
