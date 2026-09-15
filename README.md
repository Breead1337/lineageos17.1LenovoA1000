# LineageOS 17.1 (Android 10) для Lenovo A1000 (SC8830)

Здесь лежит **только то, чего нет в апстриме**: дерево устройства, вендорные
блобы, шимы и правки исходников AOSP/LineageOS. Само дерево LineageOS сюда не
выкладывается — без `.repo` и `out` оно весит десятки гигабайт, и внутри есть
файлы больше 100 МБ (жёсткий предел GitHub на файл).

## Как собрать

```sh
repo init -u https://github.com/LineageOS/android.git -b lineage-17.1
repo sync -c -j8
# содержимое этого репозитория кладётся ПОВЕРХ дерева по тем же путям
lunch lineage_a1000-userdebug
mka bacon
```

Ключи подписи (`vendor/lineage-priv`) в выкладку не входят — сгенерируйте свои.

## Что где

| путь | что |
|---|---|
| `device/lenovo/a1000/` | дерево устройства целиком, включая `prebuilt/kernel` (ядро #106, 3.10) |
| `vendor/lenovo/a1000/` | проприетарные блобы и модули ядра (mali.ko, sprdwl.ko, trout_fm.ko) |
| `external/libui_shim/` | шим под старые блобы: page flip, zero-copy, ABI libui для Q |
| `external/libsprdsensors_shim/` | шим HAL датчиков |
| `external/tinyalsa/` | ABI старого tinyalsa |
| `external/wpa_supplicant_8/` | RSSI/MAC |
| `external/noto-fonts/` | урезание шрифтов |
| `frameworks/native/` | SurfaceFlinger: перестановка каналов в шейдере (ProgramCache), принудительный GPU-композит (BufferLayer), Fence, surfaceflinger.rc |
| `hardware/interfaces/` | audio (EPERM), bluetooth 1.0 (h4, одна запись вместо writev), graphics (Gralloc0Hal, composer-шим), sensors 1.0 |
| `hardware/ril/` | libril/rild: IMEI через запрос 38, индексы приложений SIM, короткие RIL_SignalStrength v5/v6, HIDL-пул, имена сервисов по слотам |
| `hardware/marvell/` | libbt-vendor |
| `system/bt/` | BLE-гварды и возможности старого контроллера |
| `system/core/` | init (security, selinux), healthd (подсветка в зарядке), FUSE-демон sdcard |
| `system/sepolicy/` | политика SELinux (enforcing, домен `a1000_sprd`) + совместимость prebuilts/api 26–29 |
| `system/connectivity/wificond/` | netlink_utils |
| `bootable/recovery/minui/` | fbdev с переворотом страниц |
| `packages/apps/Settings/` | раздел Bluetooth, TON в буфер по «Номеру сборки» |
| `packages/apps/Trebuchet/` | ОЗУ в «недавних» |
| `packages/apps/FMRadio/`, `packages/inputmethods/LatinIME/` | правки под SC8830 |
| `vendor/lineage/charger/` | картинки экрана зарядки |
| `tools/` | скрипты, которыми накатывались все правки (`_los17_*.py`), сборка ядра (`_los17_kernel_a10.sh`), инжектор политики SELinux, разбор/пересборка boot.img |

Исходники ядра 3.10 — <https://github.com/Breead1337/lenovoa1000kernel3.10sourceENHANCED>.
Порт LineageOS 15.1 для этого же аппарата — <https://github.com/Breead1337/lineageos15.1LenovoA1000>.
