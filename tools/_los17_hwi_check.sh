#!/bin/bash
T=/home/ard/los17/hardware/interfaces
for p in audio/2.0/default/StreamOut.cpp \
         bluetooth/1.0/default/Android.mk \
         bluetooth/1.0/default/h4_protocol.cc \
         graphics/composer/2.1/default/android.hardware.graphics.composer@2.1-service.rc \
         sensors/1.0/default/Sensors.cpp; do
  [ -f "$T/$p" ] && echo "ЕСТЬ  $p" || echo "НЕТ   $p"
done
echo "=== bluetooth 1.0 default ==="; ls $T/bluetooth/1.0/default 2>/dev/null | head
echo "=== ignoredErrors в Q ==="; grep -rn "ignoredErrors" $T/audio/*/default/StreamOut.cpp 2>/dev/null | head
echo "=== CHECK_GE в Q sensors ==="; grep -rn "CHECK_GE(getHalDeviceVersion" $T/sensors/1.0/default/Sensors.cpp
echo "=== h4 в Q ==="; find $T/bluetooth -name "h4_protocol*" | head
