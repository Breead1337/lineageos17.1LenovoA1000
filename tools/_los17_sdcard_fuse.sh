#!/bin/bash
# «Камера требует SD-карту» при вставленной карте = ВНУТРЕННЕЙ ПАМЯТИ НЕТ.
#
# То же, что было на девятке (_los16_sdcard_fuse.sh): sdcard десятки умеет
# ТОЛЬКО sdcardfs/esdfs, ядро 3.10 не знает ни того, ни другого → демон падает,
# остаётся зомби, vold объявляет unmountable и emulated, и SD-карту.
#
# Берём FUSE-реализацию из дерева 8.1. Отличия десятки от девятки:
#  * vold ждёт ЧЕТВЁРТУЮ точку /mnt/runtime/full/<label> (GetDevice(mFuseFull))
#    и через 5 с объявляет таймаут — добавляем четвёртый FUSE-вид с маской 0007
#    (как sdcardfs_setup_secondary(..., dest_path_full, ..., 0007) в Q);
#  * ключи -i (default_normal) и -o (unshared_obb) — это опции sdcardfs,
#    принимаем и игнорируем.
set -e
mountpoint -q /home/ard/los17 || mount -o loop /mnt/d/los17.img /home/ard/los17
SRC=/home/ard/los15.1/system/core/sdcard
DST=/home/ard/los17/system/core/sdcard
BAK=/home/ard/sdcard.q.bak   # внутри дерева нельзя: ckati ругается на дубль модуля

[ -d $BAK ] || cp -a $DST $BAK
rm -f $DST/Android.bp $DST/sdcard.cpp
cp -f $SRC/sdcard.cpp $SRC/fuse.cpp $SRC/fuse.h $SRC/main.c $SRC/Android.mk $DST/

python3 - <<'PY'
import io
D='/home/ard/los17/system/core/sdcard/'
def sub(f, old, new):
    p=D+f; s=io.open(p,encoding='utf-8').read()
    assert s.count(old)==1, (f, old[:60])
    io.open(p,'w',encoding='utf-8',newline='\n').write(s.replace(old,new))

sub('fuse.h', '    struct fuse* fuse_write;\n',
    '    struct fuse* fuse_write;\n    struct fuse* fuse_full;   /* A1000: вид /mnt/runtime/full десятки */\n')

# уведомления об удалении должны доходить и до четвёртого вида (2 места)
p=D+'fuse.cpp'; s=io.open(p,encoding='utf-8').read()
old="""        if (fuse != fuse->global->fuse_write) {
            fuse_notify_delete(fuse->global->fuse_write, parent_node->nid, child_node->nid, name);
        }"""
new=old+"""
        if (fuse != fuse->global->fuse_full) {
            fuse_notify_delete(fuse->global->fuse_full, parent_node->nid, child_node->nid, name);
        }"""
assert s.count(old)==2
io.open(p,'w',encoding='utf-8',newline='\n').write(s.replace(old,new))

S='sdcard.cpp'
sub(S, '    struct fuse fuse_write;\n', '    struct fuse fuse_write;\n    struct fuse fuse_full;\n')
sub(S, '    struct fuse_handler handler_write;\n', '    struct fuse_handler handler_write;\n    struct fuse_handler handler_full;\n')
sub(S, '    pthread_t thread_write;\n', '    pthread_t thread_write;\n    pthread_t thread_full;\n')
sub(S, '    memset(&fuse_write, 0, sizeof(fuse_write));\n',
       '    memset(&fuse_write, 0, sizeof(fuse_write));\n    memset(&fuse_full, 0, sizeof(fuse_full));\n')
sub(S, '    memset(&handler_write, 0, sizeof(handler_write));\n',
       '    memset(&handler_write, 0, sizeof(handler_write));\n    memset(&handler_full, 0, sizeof(handler_full));\n')
sub(S, '    fuse_write.global = &global;\n', '    fuse_write.global = &global;\n    fuse_full.global = &global;\n')
sub(S, '    global.fuse_write = &fuse_write;\n', '    global.fuse_write = &fuse_write;\n    global.fuse_full = &fuse_full;\n')
sub(S, '    snprintf(fuse_write.dest_path, PATH_MAX, "/mnt/runtime/write/%s", label);\n',
       '    snprintf(fuse_write.dest_path, PATH_MAX, "/mnt/runtime/write/%s", label);\n'
       '    snprintf(fuse_full.dest_path, PATH_MAX, "/mnt/runtime/full/%s", label);\n')
sub(S, '    handler_write.fuse = &fuse_write;\n', '    handler_write.fuse = &fuse_write;\n    handler_full.fuse = &fuse_full;\n')
sub(S, '    handler_write.token = 2;\n', '    handler_write.token = 2;\n    handler_full.token = 3;\n')
sub(S, """                || fuse_setup(&fuse_write, AID_EVERYBODY, full_write ? 0007 : 0027)) {""",
       """                || fuse_setup(&fuse_write, AID_EVERYBODY, full_write ? 0007 : 0027)
                || fuse_setup(&fuse_full, AID_EVERYBODY, 0007)) {""")
sub(S, """                || fuse_setup(&fuse_write, AID_EVERYBODY, full_write ? 0007 : 0022)) {""",
       """                || fuse_setup(&fuse_write, AID_EVERYBODY, full_write ? 0007 : 0022)
                || fuse_setup(&fuse_full, AID_EVERYBODY, 0007)) {""")
sub(S, """            || pthread_create(&thread_write, NULL, start_handler, &handler_write)) {""",
       """            || pthread_create(&thread_write, NULL, start_handler, &handler_write)
            || pthread_create(&thread_full, NULL, start_handler, &handler_full)) {""")
# vold десятки после монтирования делает БЛОКИРУЮЩИЙ waitpid(mFusePid) — там
# ждут выхода sdcardfs-демона (он выходит сразу). FUSE-демон живёт вечно ->
# vold навсегда висит в doMount: StorageManagerService не стартует («Failed to
# find running mount service»), а перезагрузка виснет на vdc volume shutdown.
# Уходим в фон после монтирования и ДО создания потоков (fork копирует только
# вызывающий поток). Размонтирование vold'ом даёт ENODEV в handle_fuse_requests,
# и демон выходит сам.
sub(S, """    if (pthread_create(&thread_default, NULL, start_handler, &handler_default)""",
       """    /* A1000: vold десятки ждёт выхода процесса (waitpid без WNOHANG). */
    pid_t daemon_pid = fork();
    if (daemon_pid < 0) {
        PLOG(FATAL) << "fork failed";
    } else if (daemon_pid > 0) {
        _exit(0);
    }

    if (pthread_create(&thread_default, NULL, start_handler, &handler_default)""")
sub(S, 'getopt(argc, argv, "u:g:U:mwG")', 'getopt(argc, argv, "u:g:U:mwGio")')
sub(S, """            case 'G':
                derive_gid = true;
                break;""", """            case 'G':
                derive_gid = true;
                break;
            case 'i':
            case 'o':
                /* A1000: vold десятки передаёт -i (default_normal) и -o
                 * (unshared_obb) — это опции sdcardfs, которого в ядре 3.10
                 * нет. Принимаем молча, иначе демон уходит в usage. */
                break;""")
print('sdcard: FUSE из 8.1 + вид full + ключи -i/-o')
PY
grep -n "fuse_full\|mwGio" $DST/*.cpp $DST/*.h | head
