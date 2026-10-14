/* SPDX-License-Identifier: LGPL-2.1-or-later */
#include <ddk/ntddk.h>
__declspec(dllimport) NTSTATUS NTAPI ZwWaitForSingleObject(HANDLE, BOOLEAN, LARGE_INTEGER *);
__declspec(dllimport) NTSTATUS NTAPI ZwCreateFile(HANDLE *, ACCESS_MASK, OBJECT_ATTRIBUTES *, IO_STATUS_BLOCK *, LARGE_INTEGER *, ULONG, ULONG, ULONG, ULONG, void *, ULONG);
__declspec(dllimport) NTSTATUS NTAPI ZwWriteFile(HANDLE, HANDLE, PIO_APC_ROUTINE, void *, IO_STATUS_BLOCK *, void *, ULONG, LARGE_INTEGER *, ULONG *);
static volatile ULONG tagged, context_ok;
static ULONG cookie = 0x51a7c09e;
static void NTAPI start(void *context)
{
    ULONG_PTR caller = (ULONG_PTR)__builtin_return_address(0);
    tagged = (caller & 0xffff800000000000ULL) == 0xffff800000000000ULL;
    context_ok = context == &cookie && *(ULONG *)context == 0x51a7c09e;
    DbgPrint("NIKKE_KERNEL_THREAD tagged=%u context=%u\n", tagged, context_ok);
}
static void NTAPI unload(DRIVER_OBJECT *driver) { (void)driver; }
NTSTATUS NTAPI DriverEntry(DRIVER_OBJECT *driver, UNICODE_STRING *path)
{
    HANDLE thread;
    LARGE_INTEGER timeout;
    NTSTATUS status;
    HANDLE file;
    UNICODE_STRING name;
    OBJECT_ATTRIBUTES attributes;
    IO_STATUS_BLOCK iosb;
    ULONG result[3];
    (void)path;
    driver->DriverUnload = unload;
    status = PsCreateSystemThread(&thread, THREAD_ALL_ACCESS, NULL, NULL, NULL, start, &cookie);
    if (status) return status;
    timeout.QuadPart = -50000000;
    status = ZwWaitForSingleObject(thread, FALSE, &timeout);
    ZwClose(thread);
    result[0] = status;
    result[1] = tagged;
    result[2] = context_ok;
    RtlInitUnicodeString(&name, L"\\??\\C:\\fixtures\\kernel-thread-result.bin");
    InitializeObjectAttributes(&attributes, &name, OBJ_CASE_INSENSITIVE, NULL, NULL);
    if (!ZwCreateFile(&file, FILE_WRITE_DATA | SYNCHRONIZE, &attributes, &iosb,
                      NULL, 0, FILE_SHARE_READ, FILE_OVERWRITE_IF,
                      FILE_SYNCHRONOUS_IO_NONALERT, NULL, 0))
    {
        ZwWriteFile(file, NULL, NULL, NULL, &iosb, result, sizeof(result), NULL, NULL);
        ZwClose(file);
    }
    DbgPrint("NIKKE_KERNEL_THREAD wait=%08x tagged=%u context=%u\n", status, tagged, context_ok);
    return !status && tagged && context_ok ? STATUS_SUCCESS : STATUS_UNSUCCESSFUL;
}
