#!/bin/bash
F=/home/ard/los17/hardware/ril/libril/ril_service.cpp
echo "=== файл: $(wc -l < $F) строк ==="
grep -n "^namespace \|^int radio::getIccCardStatusResponse\|^int radio_1_4::getIccCardStatusResponse\|getDeviceIdentity(int32_t serial)\|getSignalStrengthResponse\|convertRilSignalStrengthToHal" $F | head -20
echo "=== ril_commands.h GET_IMEI ==="
grep -n "RIL_REQUEST_GET_IMEI" /home/ard/los17/hardware/ril/libril/ril_commands.h
