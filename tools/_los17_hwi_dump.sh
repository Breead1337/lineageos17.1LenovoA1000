#!/bin/bash
T=/home/ard/los17/hardware/interfaces
sed -n "80,97p" $T/bluetooth/1.0/default/h4_protocol.cc
echo "=== sensors 90-110 ==="
sed -n "88,110p" $T/sensors/1.0/default/Sensors.cpp
echo "=== composer rc ==="
cat "$T/graphics/composer/2.1/default/android.hardware.graphics.composer@2.1-service.rc"
