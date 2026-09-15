#!/bin/bash
sed -n "20,45p" /home/ard/los17/hardware/ril/rild/Android.mk
echo "=== что было в 8.1 ==="
sed -n "20,40p" /home/ard/los15.1/hardware/ril/rild/Android.mk
echo "=== a1000_ril.rc в дереве устройства ==="
find /home/ard/los17/device/lenovo/a1000 -name "*ril*"
