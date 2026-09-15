#!/bin/bash
T=/home/ard/los17
echo "=== allocator 2.0 utils ==="
find $T/hardware/interfaces/graphics/allocator/2.0/utils -name "*.h" | head
echo "=== mapper 2.0 utils ==="
find $T/hardware/interfaces/graphics/mapper/2.0/utils -name "*.h" | head
echo "=== Gralloc0 в Q ==="
grep -rln "Gralloc0" $T/hardware/interfaces/graphics/ | head
echo
echo "=== как это выглядело в 8.1 ==="
ls /home/ard/los15.1/hardware/interfaces/graphics/allocator/2.0/default/
