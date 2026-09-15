#!/bin/bash
timeout 90 git ls-remote --tags https://github.com/aosp-mirror/platform_system_tools_hidl 2>&1 | tail -5
echo "rc=$?"
echo "--- сколько тегов android-10"
timeout 90 git ls-remote --tags https://github.com/aosp-mirror/platform_system_tools_hidl 2>/dev/null | grep -c "android-10"
