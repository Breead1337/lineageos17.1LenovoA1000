#!/bin/bash
cd /home/ard/los17
echo "=== проекты с remote=aosp в манифестах ==="
grep -h 'remote="aosp"' .repo/manifests/*.xml .repo/manifests/snippets/*.xml 2>/dev/null \
 | sed -E 's/^\s*//' | head -40
echo
echo "=== сколько всего ==="
grep -h 'remote="aosp"' .repo/manifests/*.xml .repo/manifests/snippets/*.xml 2>/dev/null | wc -l
echo "=== определение remote aosp ==="
grep -h '<remote' .repo/manifests/default.xml
