# Copyright (C) 2014 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ifneq ($(BOARD_HAVE_QCOM_FM),true)
ifneq ($(BOARD_HAVE_BCM_FM),true)
ifneq ($(BOARD_HAVE_SLSI_FM),true)

LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

# A1000: fmr_core.cpp и common.cpp — реализация под MediaTek (/dev/fm,
# libfmcust.so). У нас Spreadtrum sr2351 с собственным драйвером, поэтому они
# заменены на fmr_core_sc8830.cpp. libfm_jni.cpp и fmr_err.cpp общие.
LOCAL_SRC_FILES := \
    fmr_core_sc8830.cpp \
    fmr_err.cpp \
    libfm_jni.cpp

LOCAL_C_INCLUDES := $(JNI_H_INCLUDE) \
    frameworks/base/include/media

LOCAL_SHARED_LIBRARIES := \
    libcutils \
    libdl \
    libmedia \
    liblog

LOCAL_MODULE := libfmjni

# A1000: апстримный libfm_jni.cpp не использует env/thiz в двух десятках
# функций, а в десятке к модулю приезжает -Werror. Гасим точечно.
LOCAL_CFLAGS += -Wno-unused-parameter -Wno-unused-variable
LOCAL_MODULE_TAGS := optional

include $(BUILD_SHARED_LIBRARY)

endif # BOARD_HAVE_SLSI_FM
endif # BOARD_HAVE_BCM_FM
endif # BOARD_HAVE_QCOM_FM
