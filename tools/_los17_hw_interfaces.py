# -*- coding: utf-8 -*-
# LOS 17.1 / A1000: правки HAL-обвязки (перенос из 8.1).
#
#  1) audio: стоковый HAL Spreadtrum отдаёт EPERM на запрос позиции
#     воспроизведения — это не ошибка, а «не умею», но лог заливался ALOGW на
#     каждый буфер. В десятке файл переехал в audio/core/all-versions/default.
#  2) bluetooth h4: /dev/sttybt0 — не UART, а SIPC-канал к WCN-чипу. writev в
#     ядре 3.10 разваливается на два write(), контроллер получает байт типа
#     отдельно от тела и команду не разбирает. Плюс не убиваем HAL из-за
#     мусорного байта после заливки pskey.
#  3) bluetooth: init-скрипт AOSP не ставим, сервис объявлен в a1000_bt.rc.
#  4) composer: тот же шим вывода кадра, что и у surfaceflinger.
#  5) sensors: блоб рапортует SENSORS_DEVICE_API_VERSION_1_0, а CHECK_GE(1_3)
#     фатален — сервис умирал на старте и загрузка вставала.
import io

T = '/home/ard/los17/hardware/interfaces/'

# ---------- 1. audio: EPERM не считаем ошибкой ----------
P = T + 'audio/core/all-versions/default/StreamOut.cpp'
s = io.open(P, encoding='utf-8').read()
if 'A1000' in s:
    print('StreamOut.cpp: uzhe pravlen')
else:
    old = "    static const std::vector<int> ignoredErrors{EINVAL, EAGAIN, ENODATA};"
    new = ("    // A1000: стоковый HAL Spreadtrum отдаёт здесь EPERM — он просто не умеет\n"
           "    // сообщать позицию воспроизведения. Это такой же штатный «позиции нет»,\n"
           "    // как EINVAL/ENODATA, но без него ALOGW ниже срабатывал на КАЖДЫЙ буфер\n"
           "    // и заливал лог десятками строк в секунду.\n"
           "    static const std::vector<int> ignoredErrors{EINVAL, EAGAIN, ENODATA, EPERM};")
    assert old in s, 'ne nayden ignoredErrors'
    io.open(P, 'w', encoding='utf-8').write(s.replace(old, new, 1))
    print('StreamOut.cpp: EPERM v ignoredErrors')

# ---------- 2. bluetooth h4: одна запись + ресинхронизация ----------
P = T + 'bluetooth/1.0/default/h4_protocol.cc'
s = io.open(P, encoding='utf-8').read()
if 'A1000' in s:
    print('h4_protocol.cc: uzhe pravlen')
else:
    if '#include <vector>' not in s:
        s = s.replace('#include <sys/uio.h>', '#include <sys/uio.h>\n#include <vector>', 1)
    old = """  struct iovec iov[] = {{&type, sizeof(type)},
                        {const_cast<uint8_t*>(data), length}};
  ssize_t ret = 0;
  do {
    ret =
        TEMP_FAILURE_RETRY(writev(uart_fd_, iov, sizeof(iov) / sizeof(iov[0])));
  } while (-1 == ret && EAGAIN == errno);"""
    new = """  // A1000: одна запись вместо writev. /dev/sttybt0 — не UART, а SIPC-канал к
  // WCN-чипу, и каждая запись уходит туда отдельным сообщением. writev в ядре
  // 3.10 для tty разваливается на два write(), контроллер получает байт типа
  // отдельно от тела и команду не разбирает.
  std::vector<uint8_t> packet;
  packet.reserve(length + 1);
  packet.push_back(type);
  packet.insert(packet.end(), data, data + length);
  ssize_t ret = 0;
  do {
    ret = TEMP_FAILURE_RETRY(write(uart_fd_, packet.data(), packet.size()));
  } while (-1 == ret && EAGAIN == errno);"""
    assert old in s, 'ne nayden Send/writev'
    s = s.replace(old, new, 1)

    old = """    hci_packet_type_ = static_cast<HciPacketType>(buffer[0]);
    if (hci_packet_type_ != HCI_PACKET_TYPE_ACL_DATA &&
        hci_packet_type_ != HCI_PACKET_TYPE_SCO_DATA &&
        hci_packet_type_ != HCI_PACKET_TYPE_EVENT) {
      LOG_ALWAYS_FATAL("%s: Unimplemented packet type %d", __func__,
                       static_cast<int>(hci_packet_type_));
    }"""
    new = """    hci_packet_type_ = static_cast<HciPacketType>(buffer[0]);
    if (hci_packet_type_ != HCI_PACKET_TYPE_ACL_DATA &&
        hci_packet_type_ != HCI_PACKET_TYPE_SCO_DATA &&
        hci_packet_type_ != HCI_PACKET_TYPE_EVENT) {
      // A1000: sprd-контроллер после заливки pskey оставляет в канале хвост
      // ответа, который вендорская либа не дочитала. Убивать из-за него весь
      // HAL нельзя — просто ресинхронизируемся на следующем байте.
      ALOGE("%s: skipping unexpected type byte 0x%02x", __func__,
            static_cast<unsigned int>(buffer[0]));
      hci_packet_type_ = HCI_PACKET_TYPE_UNKNOWN;
      return;
    }"""
    assert old in s, 'ne nayden OnDataReady'
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('h4_protocol.cc: odna zapis + resync')

# ---------- 3. bluetooth: без своего init-скрипта ----------
P = T + 'bluetooth/1.0/default/Android.bp'
s = io.open(P, encoding='utf-8').read()
if 'A1000' in s:
    print('bluetooth Android.bp: uzhe pravlen')
else:
    old = """    init_rc: ["android.hardware.bluetooth@1.0-service.rc"],
    srcs: ["service.cpp"],"""
    new = """    // A1000: init-скрипт AOSP не ставим — сервис bluetooth-1-0 объявлен в
    // a1000_bt.rc (нужны свои права на /dev/sttybt0 и порядок запуска).
    srcs: ["service.cpp"],"""
    assert old in s, 'ne nayden init_rc bluetooth'
    io.open(P, 'w', encoding='utf-8').write(s.replace(old, new, 1))
    print('bluetooth Android.bp: bez init_rc')

# ---------- 4. composer: шим вывода ----------
P = T + 'graphics/composer/2.1/default/android.hardware.graphics.composer@2.1-service.rc'
s = io.open(P, encoding='utf-8').read()
if 'libui_shim' in s:
    print('composer rc: uzhe pravlen')
else:
    old = "    capabilities SYS_NICE"
    new = "    capabilities SYS_NICE\n    setenv LD_PRELOAD libui_shim.so"
    assert old in s, 'ne naydeny capabilities'
    io.open(P, 'w', encoding='utf-8').write(s.replace(old, new, 1))
    print('composer rc: LD_PRELOAD libui_shim.so')

# ---------- 5. sensors: принимаем HAL 1.0 ----------
P = T + 'sensors/1.0/default/Sensors.cpp'
s = io.open(P, encoding='utf-8').read()
if 'A1000' in s:
    print('Sensors.cpp: uzhe pravlen')
else:
    old = """    // Require all the old HAL APIs to be present except for injection, which
    // is considered optional.
    CHECK_GE(getHalDeviceVersion(), SENSORS_DEVICE_API_VERSION_1_3);"""
    new = """    // A1000: принимаем старый HAL 1.0. Вендорный блоб рапортует
    // SENSORS_DEVICE_API_VERSION_1_0 (0x01000001), а CHECK_GE против 1_3
    // фатален — сервис умирал на старте и загрузка вставала. Обязательны на
    // деле только базовые точки входа; всё, что добавили после 1_0,
    // проверяется на nullptr в месте вызова, и это безопасно: размер
    // sensors_poll_device_1_t неизменен на всей ветке 1.x.
    CHECK_GE(getHalDeviceVersion(), SENSORS_DEVICE_API_VERSION_1_0);
    if (getHalDeviceVersion() < SENSORS_DEVICE_API_VERSION_1_3) {
        LOG(WARNING) << "HAL reports version "
                     << std::hex << getHalDeviceVersion() << std::dec
                     << ", running in legacy mode";
    }
    CHECK(mSensorDevice->activate != nullptr);
    CHECK(mSensorDevice->poll != nullptr);"""
    assert old in s, 'ne nayden CHECK_GE'
    io.open(P, 'w', encoding='utf-8').write(s.replace(old, new, 1))
    print('Sensors.cpp: HAL 1.0 prinimaetsya')
