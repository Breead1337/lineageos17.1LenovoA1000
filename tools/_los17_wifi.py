# -*- coding: utf-8 -*-
u"""A1000 / LOS 17.1: Wi-Fi — деления сигнала и MAC-адрес (правки 8.1/9 под десятку).

1. wificond: sprdwl не отдаёт NL80211_STA_INFO_TX_FAILED, GetStationInfo()
   падал целиком → «Invalid signal poll result» → RSSI -127, иконка без делений.
   В десятке TX_BITRATE уже необязателен; делаем необязательными и TX_PACKETS/
   TX_FAILED, обязателен только SIGNAL (см. build_wificond_rssi.sh для 8.1).
2. wpa_supplicant (hidl/1.2): MAC узнаётся только приватной командой MACADDR,
   sprdwl её не знает → FAILURE_UNKNOWN. Фабричного MAC через vendor HAL у нас
   нет, и ClientModeImpl откатывается на supplicant → «MAC: <none>» и пусто в
   «О телефоне». Запасной путь — wpa_s->own_addr (см. _los16_wifi_mac.py).
"""
import io

T = '/home/ard/los17/'


def patch(path, old, new, mark):
    s = io.open(T + path, encoding='utf-8', errors='surrogateescape').read()
    if mark in s:
        print(path + u': уже')
        return
    assert old in s, path + u': блок не найден'
    io.open(T + path, 'w', encoding='utf-8', errors='surrogateescape',
            newline='\n').write(s.replace(old, new, 1))
    print(path + u': пропатчен')


patch('system/connectivity/wificond/net/netlink_utils.cpp',
      """  int32_t tx_good, tx_bad;
  if (!sta_info.GetAttributeValue(NL80211_STA_INFO_TX_PACKETS, &tx_good)) {
    LOG(ERROR) << "Failed to get NL80211_STA_INFO_TX_PACKETS";
    return false;
  }
  if (!sta_info.GetAttributeValue(NL80211_STA_INFO_TX_FAILED, &tx_bad)) {
    LOG(ERROR) << "Failed to get NL80211_STA_INFO_TX_FAILED";
    return false;
  }
""",
      """  // A1000: sprdwl не отдаёт часть полей станции; раньше это роняло весь
  // опрос вместе с RSSI (-127, иконка без делений). Обязателен только SIGNAL.
  int32_t tx_good = 0, tx_bad = 0;
  if (!sta_info.GetAttributeValue(NL80211_STA_INFO_TX_PACKETS, &tx_good)) {
    tx_good = 0;
  }
  if (!sta_info.GetAttributeValue(NL80211_STA_INFO_TX_FAILED, &tx_bad)) {
    tx_bad = 0;
  }
""", 'A1000: sprdwl')

patch('external/wpa_supplicant_8/wpa_supplicant/hidl/1.2/sta_iface.cpp',
      '\t    reply_str.find("=") == std::string::npos) {\n'
      '\t\treturn {{SupplicantStatusCode::FAILURE_UNKNOWN, ""}, {}};\n'
      '\t}\n',
      '\t    reply_str.find("=") == std::string::npos) {\n'
      '\t\t/* A1000: sprdwl не знает MACADDR — берём собственный адрес\n'
      '\t\t * интерфейса, иначе в настройках пустой MAC-адрес Wi-Fi. */\n'
      '\t\tif (!is_zero_ether_addr(wpa_s->own_addr)) {\n'
      '\t\t\tstd::array<uint8_t, 6> own_addr;\n'
      '\t\t\tos_memcpy(own_addr.data(), wpa_s->own_addr, ETH_ALEN);\n'
      '\t\t\treturn {{SupplicantStatusCode::SUCCESS, ""}, own_addr};\n'
      '\t\t}\n'
      '\t\treturn {{SupplicantStatusCode::FAILURE_UNKNOWN, ""}, {}};\n'
      '\t}\n', 'A1000: sprdwl')
