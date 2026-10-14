/* SPDX-License-Identifier: LGPL-2.1-or-later */
#include <ddk/ntifs.h>
__declspec(dllimport) NTSTATUS NTAPI ZwCreateFile(HANDLE *, ACCESS_MASK, OBJECT_ATTRIBUTES *, IO_STATUS_BLOCK *, LARGE_INTEGER *, ULONG, ULONG, ULONG, ULONG, void *, ULONG);
__declspec(dllimport) NTSTATUS NTAPI ZwWriteFile(HANDLE, HANDLE, PIO_APC_ROUTINE, void *, IO_STATUS_BLOCK *, void *, ULONG, LARGE_INTEGER *, ULONG *);
static KEVENT event;
static WORK_QUEUE_ITEM items[2];
static ULONG cookie[2] = {0x127bdfe1, 0x387acc54};
static volatile ULONG result[8];
static HANDLE origin;
static void NTAPI worker(void *context)
{
    unsigned i = context == &cookie[1];
    UNICODE_STRING symbol;
    PETHREAD (NTAPI *get_thread)(void);
    ULONG_PTR caller = (ULONG_PTR)__builtin_return_address(0);
    RtlInitUnicodeString(&symbol, L"KeGetCurrentThread");
    get_thread = (void *)MmGetSystemRoutineAddress(&symbol);
    result[i*4] = context == &cookie[i] && cookie[i] == (i ? 0x387acc54 : 0x127bdfe1);
    result[i*4+1] = PsGetCurrentProcessId() == (HANDLE)4 && PsIsSystemThread(get_thread());
    result[i*4+2] = PsGetCurrentThreadId() != origin;
    result[i*4+3] = (caller & 0xffff800000000000ULL) == 0xffff800000000000ULL;
    KeSetEvent(&event, 0, FALSE);
}
static void NTAPI unload(DRIVER_OBJECT *driver) { (void)driver; }
NTSTATUS NTAPI DriverEntry(DRIVER_OBJECT *driver, UNICODE_STRING *path)
{
    HANDLE file;
    LARGE_INTEGER timeout;
    NTSTATUS status;
    UNICODE_STRING name;
    OBJECT_ATTRIBUTES attributes;
    IO_STATUS_BLOCK iosb;
    unsigned i;
    (void)path;
    driver->DriverUnload = unload;
    origin = PsGetCurrentThreadId();
    for (i = 0; i < 2; ++i)
    {
        KeInitializeEvent(&event, SynchronizationEvent, FALSE);
        ExInitializeWorkItem(&items[i], worker, &cookie[i]);
        ExQueueWorkItem(&items[i], i ? DelayedWorkQueue : CriticalWorkQueue);
        timeout.QuadPart = -50000000;
        status = KeWaitForSingleObject(&event, Executive, KernelMode, FALSE, &timeout);
        if (status) return status;
    }
    RtlInitUnicodeString(&name, L"\\??\\C:\\fixtures\\ex-work-item-result.bin");
    InitializeObjectAttributes(&attributes, &name, OBJ_CASE_INSENSITIVE, NULL, NULL);
    status = ZwCreateFile(&file, FILE_WRITE_DATA | SYNCHRONIZE, &attributes, &iosb,
                         NULL, 0, FILE_SHARE_READ, FILE_OVERWRITE_IF, FILE_SYNCHRONOUS_IO_NONALERT, NULL, 0);
    if (status) return status;
    ZwWriteFile(file, NULL, NULL, NULL, &iosb, (void *)result, sizeof(result), NULL, NULL);
    ZwClose(file);
    for (i = 0; i < 8; ++i) if (!result[i]) return STATUS_UNSUCCESSFUL;
    return STATUS_SUCCESS;
}
