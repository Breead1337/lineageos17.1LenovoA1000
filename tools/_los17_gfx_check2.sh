#!/bin/bash
T=/home/ard/los17
echo "=== allocator 2.0 default ==="
ls $T/hardware/interfaces/graphics/allocator/2.0/default/
echo "=== модули libgralloc1on0adapter / libhwc2on1adapter в 17.1 ==="
grep -rn "libgralloc1on0adapter" $T/hardware/interfaces/graphics/allocator/2.0/default/Android.bp $T/hardware/libhardware/Android.bp 2>/dev/null | head
grep -rln "name: \"libgralloc1on0adapter\"\|LOCAL_MODULE := libgralloc1on0adapter" $T/hardware $T/frameworks 2>/dev/null | head -3
grep -rln "name: \"libhwc2on1adapter\"" $T/hardware $T/frameworks 2>/dev/null | head -3
