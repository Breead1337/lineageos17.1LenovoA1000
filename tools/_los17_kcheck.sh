#!/bin/bash
# Что уже есть в нашем defconfig из требований Android 10.
K=/home/ard/a1000-kernel
D=$K/arch/arm/configs/a1000_baton4iks_defconfig
cd $K
echo "=== ветка/статус ядра ==="
git log --oneline -3 | cat
git status --short | head -20
echo
echo "=== defconfig: $(wc -l < $D) строк ==="
for s in ANDROID_BINDER_IPC ANDROID_BINDER_DEVICES ANDROID_BINDER_IPC_32BIT ASHMEM ION \
         CPUSETS CGROUPS CGROUP_SCHED MEMCG MEMCG_SWAP SCHED_TUNE FREEZER \
         SDCARD_FS FUSE_FS QUOTA QFMT_V2 QUOTACTL QUOTA_TREE \
         NETFILTER_XT_MATCH_QTAGUID NETFILTER_XT_MATCH_OWNER ANDROID_PARANOID_NETWORK \
         NETFILTER_XT_MATCH_SOCKET NETFILTER_XT_TARGET_IDLETIMER INET_UDP_DIAG INET_DIAG_DESTROY \
         ANDROID_LOW_MEMORY_KILLER SECURITY_SELINUX SECURITY_SELINUX_BOOTPARAM \
         XFRM_USER NET_KEY INET_ESP IP_NF_NAT NF_CONNTRACK PSI ZRAM ZSMALLOC \
         UID_SYS_STATS RD_LZ4 SYNC SW_SYNC STAGING ARM_UNWIND FHANDLE \
         SECCOMP TMPFS_POSIX_ACL DM_VERITY OVERLAY_FS IKCONFIG; do
  v=$(grep -E "^(CONFIG_$s=|# CONFIG_$s )" $D | head -1)
  printf "%-36s %s\n" "$s" "${v:- ОТСУТСТВУЕТ}"
done
