#!/bin/bash
F=/home/ard/los17/hardware/ril/libril/ril_service.cpp
echo "########## getDeviceIdentity (1919) ##########"; sed -n "1919,1930p" $F
echo "########## getIccCardStatusResponse (3022-3075) ##########"; sed -n "3022,3075p" $F
echo "########## getSignalStrengthResponse (3484,3502) ##########"; sed -n "3484,3502p" $F
echo "########## getDeviceIdentityResponse ##########"; grep -n -A18 "^int radio::getDeviceIdentityResponse" $F | head -30
echo "########## radioStateChangedInd ##########"; grep -n -B2 -A10 "^int radio::radioStateChangedInd" $F
echo "########## convertRilSignalStrengthToHal (7192) ##########"; sed -n "7192,7205p" $F
echo "########## currentSignalStrengthInd ##########"; grep -n -A12 "^int radio::currentSignalStrengthInd" $F | head -16
echo "########## rild.c ##########"; grep -n -B3 -A10 "MAX_RILDS" /home/ard/los17/hardware/ril/rild/rild.c | head -30
echo "########## rild/Android.mk LOCAL_INIT_RC ##########"; grep -n "LOCAL_INIT_RC" /home/ard/los17/hardware/ril/rild/Android.mk
