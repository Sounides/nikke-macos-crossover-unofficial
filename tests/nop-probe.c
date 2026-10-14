/* SPDX-License-Identifier: LGPL-2.1-or-later */
#include <windows.h>
#include <stdio.h>
#include <string.h>

static LONG WINAPI fail(EXCEPTION_POINTERS *p)
{
    printf("NOP_REG_FAULT code=0x%08lx\n", p->ExceptionRecord->ExceptionCode);
    fflush(stdout);
    ExitProcess(2);
    return EXCEPTION_EXECUTE_HANDLER;
}

__attribute__((noinline)) static void nop_register(void)
{
    __asm__ volatile(".byte 0x0f, 0x1f, 0xc1");
}

__attribute__((noinline)) static void illegal_ud2(void)
{
    __asm__ volatile(".byte 0x0f, 0x0b");
}

__attribute__((noinline)) static void illegal_lock_nop(void)
{
    __asm__ volatile(".byte 0xf0, 0x0f, 0x1f, 0xc1");
}

__attribute__((noinline)) static void nop_memory(void)
{
    __asm__ volatile(".byte 0x66, 0x0f, 0x1f, 0x84, 0x00, 0, 0, 0, 0");
}

int main(int argc, char **argv)
{
    SetUnhandledExceptionFilter(fail);
    printf("Testing register-form multi-byte NOP\n");
    fflush(stdout);
    if (argc > 1 && !strcmp(argv[1], "ud2")) illegal_ud2();
    else if (argc > 1 && !strcmp(argv[1], "lock")) illegal_lock_nop();
    else if (argc > 1 && !strcmp(argv[1], "memory")) nop_memory();
    else nop_register();
    printf("NOP_REG_PASS\n");
    return 0;
}
