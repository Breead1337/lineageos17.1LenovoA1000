#!/bin/bash
T=/home/ard/los17/hardware/interfaces
echo "=== где ignoredErrors в Q ==="
grep -rn "ignoredErrors" $T/audio 2>/dev/null | head -3
echo "=== bluetooth Android.bp init_rc ==="
grep -n -B4 -A2 "init_rc" $T/bluetooth/1.0/default/Android.bp | head -20
echo "=== h4_protocol Send ==="
sed -n "/size_t H4Protocol::Send/,/^}/p" $T/bluetooth/1.0/default/h4_protocol.cc
echo "=== h4_protocol OnDataReady фрагмент ==="
grep -n -A10 "Unimplemented packet type" $T/bluetooth/1.0/default/h4_protocol.cc
