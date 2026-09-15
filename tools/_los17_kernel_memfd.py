# -*- coding: utf-8 -*-
u"""A1000 / Android 10: бэкпорт memfd_create в ядро 3.10.

ЗАЧЕМ. Из logcat упавшей загрузки:
    system_server: Could not reset JIT state after zygote fork:
        Failed to initialize dual view JIT. memfd_create() error: Function not implemented
    F libc: Fatal signal 11 (SIGSEGV), code 2 (SEGV_ACCERR) ... (Jit thread pool)
      #00 mspace_malloc  #02 art::jit::JitCodeCache::CommitCodeInternal
      #04 art::OptimizingCompiler::JitCompile

ART десятки держит кеш JIT ДВУМЯ отображениями одной и той же памяти: одно
на запись, второе на исполнение. Делается это через memfd_create(2) —
безымянный файл в tmpfs, который потом отображается дважды. Вызов появился в
ядре 3.17 (11f75a01448f "shm: add memfd_create()"), в 3.10 его нет.

Запасного пути нет: в art/runtime/jit/jit_code_cache.cc есть только вариант с
одним отображением RWX, и он разрешён лишь при rwx_memory_allowed —
    if (!rwx_memory_allowed) { *error_msg = oss.str(); return false; }
Здесь это не разрешено, поэтому JIT остаётся неинициализированным, а первая же
компиляция пишет в страницу без права записи → SIGSEGV → system_server падает
по кругу и загрузка не завершается.

ЧТО ДЕЛАЕМ. Переносим сам вызов, без печатей (F_SEAL_*): печати живут в
shmem_inode_info и тянут за собой заметный кусок mm/shmem.c, а ART их не
просит (флаги = 0). MFD_ALLOW_SEALING честно отклоняем -EINVAL, чтобы никто не
считал, что запечатал память, когда это не так.
# ponytail: memfd без печатей; если появится потребитель F_ADD_SEALS —
# переносить seals из 3.17 целиком.

Номер вызова на ARM — 385 (после seccomp=383 и getrandom=384). 384 оставляем
заглушкой sys_ni_syscall: getrandom тут не нужен, bionic откатывается на
/dev/urandom, а сдвигать нумерацию нельзя — она общая с userspace.
"""
import io, os

K = '/home/ard/a1000-kernel'


def edit(path, old, new, mark):
    p = os.path.join(K, path)
    s = io.open(p, encoding='utf-8', errors='surrogateescape').read()
    if mark in s:
        print(u'%s: уже правлен' % path)
        return False
    assert old in s, u'%s: не найден якорь' % path
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', errors='surrogateescape', newline='\n').write(s)
    print(u'%s: правка внесена' % path)
    return True


# 1. номера вызовов ----------------------------------------------------------
edit('arch/arm/include/uapi/asm/unistd.h',
     '#define __NR_seccomp\t\t\t(__NR_SYSCALL_BASE+383)\n',
     '#define __NR_seccomp\t\t\t(__NR_SYSCALL_BASE+383)\n'
     '/* A1000: 384 (getrandom) не переносим, но номер занят навсегда. */\n'
     '#define __NR_memfd_create\t\t(__NR_SYSCALL_BASE+385)\n',
     '__NR_memfd_create')

# 2. размер таблицы (кратен четырём — см. syscalls_padding в calls.S) --------
edit('arch/arm/include/asm/unistd.h',
     '#define __NR_syscalls  (384)',
     '#define __NR_syscalls  (388)',
     '(388)')

# 3. сама таблица ------------------------------------------------------------
edit('arch/arm/kernel/calls.S',
     '\t\tCALL(sys_seccomp)\n',
     '\t\tCALL(sys_seccomp)\n'
     '/* 384 */\tCALL(sys_ni_syscall)\t\t/* reserved sys_getrandom     */\n'
     '\t\tCALL(sys_memfd_create)\n',
     'sys_memfd_create')

# 4. заголовок с флагами -----------------------------------------------------
H = os.path.join(K, 'include/uapi/linux/memfd.h')
if os.path.exists(H):
    print(u'include/uapi/linux/memfd.h: уже есть')
else:
    io.open(H, 'w', encoding='utf-8', newline='\n').write(
        u'#ifndef _UAPI_LINUX_MEMFD_H\n'
        u'#define _UAPI_LINUX_MEMFD_H\n'
        u'\n'
        u'/* flags for memfd_create(2) (unsigned int) */\n'
        u'#define MFD_CLOEXEC\t\t0x0001U\n'
        u'#define MFD_ALLOW_SEALING\t0x0002U\n'
        u'\n'
        u'#endif /* _UAPI_LINUX_MEMFD_H */\n')
    print(u'include/uapi/linux/memfd.h: создан')

# 5. прототип ----------------------------------------------------------------
edit('include/linux/syscalls.h',
     'asmlinkage long sys_seccomp(unsigned int op, unsigned int flags,\n',
     'asmlinkage long sys_memfd_create(const char __user *uname_ptr, unsigned int flags);\n'
     'asmlinkage long sys_seccomp(unsigned int op, unsigned int flags,\n',
     'sys_memfd_create')

# 6. реализация --------------------------------------------------------------
edit('mm/shmem.c',
     '#include <linux/xattr.h>\n',
     '#include <linux/xattr.h>\n'
     '#include <linux/syscalls.h>\n'
     '#include <uapi/linux/memfd.h>\n',
     '<uapi/linux/memfd.h>')

BODY = u'''
/*
 * A1000: memfd_create(2), бэкпорт из 3.17 (11f75a01448f). Нужен ART десятки:
 * кеш JIT держится двумя отображениями одного безымянного файла tmpfs.
 * Печати (F_SEAL_*) НЕ перенесены — см. _los17_kernel_memfd.py.
 */
#define MFD_NAME_PREFIX "memfd:"
#define MFD_NAME_PREFIX_LEN (sizeof(MFD_NAME_PREFIX) - 1)
#define MFD_NAME_MAX_LEN (NAME_MAX - MFD_NAME_PREFIX_LEN)

#define MFD_ALL_FLAGS (MFD_CLOEXEC | MFD_ALLOW_SEALING)

SYSCALL_DEFINE2(memfd_create,
\t\tconst char __user *, uname,
\t\tunsigned int, flags)
{
\tstruct file *file;
\tint fd, error;
\tchar *name;
\tlong len;

\tif (flags & ~(unsigned int)MFD_ALL_FLAGS)
\t\treturn -EINVAL;

\t/* Печатей в этом ядре нет. Молча делать вид, что запечатали, нельзя. */
\tif (flags & MFD_ALLOW_SEALING)
\t\treturn -EINVAL;

\t/* длина считается вместе с завершающим нулём */
\tlen = strnlen_user(uname, MFD_NAME_MAX_LEN + 1);
\tif (len <= 0)
\t\treturn -EFAULT;
\tif (len > MFD_NAME_MAX_LEN + 1)
\t\treturn -EINVAL;

\tname = kmalloc(len + MFD_NAME_PREFIX_LEN, GFP_KERNEL);
\tif (!name)
\t\treturn -ENOMEM;

\tstrcpy(name, MFD_NAME_PREFIX);
\tif (copy_from_user(&name[MFD_NAME_PREFIX_LEN], uname, len)) {
\t\terror = -EFAULT;
\t\tgoto err_name;
\t}

\t/* завершающий ноль мог измениться после strnlen_user() */
\tif (name[len + MFD_NAME_PREFIX_LEN - 1]) {
\t\terror = -EFAULT;
\t\tgoto err_name;
\t}

\tfd = get_unused_fd_flags((flags & MFD_CLOEXEC) ? O_CLOEXEC : 0);
\tif (fd < 0) {
\t\terror = fd;
\t\tgoto err_name;
\t}

\tfile = shmem_file_setup(name, 0, VM_NORESERVE);
\tif (IS_ERR(file)) {
\t\terror = PTR_ERR(file);
\t\tgoto err_fd;
\t}
\tfile->f_mode |= FMODE_LSEEK | FMODE_PREAD | FMODE_PWRITE;
\tfile->f_flags |= O_RDWR | O_LARGEFILE;

\tfd_install(fd, file);
\tkfree(name);
\treturn fd;

err_fd:
\tput_unused_fd(fd);
err_name:
\tkfree(name);
\treturn error;
}
'''

p = os.path.join(K, 'mm/shmem.c')
s = io.open(p, encoding='utf-8', errors='surrogateescape').read()
if 'SYSCALL_DEFINE2(memfd_create' in s:
    print(u'mm/shmem.c: тело memfd_create уже на месте')
else:
    anchor = 'EXPORT_SYMBOL_GPL(shmem_file_setup);\n'
    assert anchor in s, u'mm/shmem.c: не найден якорь shmem_file_setup'
    s = s.replace(anchor, anchor + BODY, 1)
    io.open(p, 'w', encoding='utf-8', errors='surrogateescape', newline='\n').write(s)
    print(u'mm/shmem.c: добавлен memfd_create')
