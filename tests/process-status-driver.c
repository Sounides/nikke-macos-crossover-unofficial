/* SPDX-License-Identifier: LGPL-2.1-or-later */
#include <ddk/ntddk.h>
__declspec(dllimport) NTSTATUS NTAPI PsGetProcessExitStatus(PEPROCESS process);
__declspec(dllimport) NTSTATUS NTAPI PsLookupProcessByProcessId(HANDLE id, PEPROCESS *process);
__declspec(dllimport) NTSTATUS NTAPI PsLookupThreadByThreadId(HANDLE id, PETHREAD *thread);
__declspec(dllimport) NTSTATUS NTAPI PsGetContextThread(PETHREAD thread, CONTEXT *context, KPROCESSOR_MODE mode);
#define IOCTL_HOLD CTL_CODE(FILE_DEVICE_UNKNOWN, 0x800, METHOD_BUFFERED, FILE_ANY_ACCESS)
#define IOCTL_STATUS CTL_CODE(FILE_DEVICE_UNKNOWN, 0x801, METHOD_BUFFERED, FILE_ANY_ACCESS)
static PEPROCESS held_process;
static UNICODE_STRING link_name;

static NTSTATUS NTAPI dispatch(DEVICE_OBJECT *device, IRP *irp)
{
    IO_STACK_LOCATION *stack = IoGetCurrentIrpStackLocation(irp);
    NTSTATUS status = STATUS_SUCCESS;
    ULONG_PTR length = 0;
    (void)device;
    if (stack->MajorFunction == IRP_MJ_DEVICE_CONTROL)
    {
        ULONG code = stack->Parameters.DeviceIoControl.IoControlCode;
        if (stack->Parameters.DeviceIoControl.OutputBufferLength < sizeof(NTSTATUS))
            status = STATUS_BUFFER_TOO_SMALL;
        else if (code == IOCTL_HOLD && stack->Parameters.DeviceIoControl.InputBufferLength >= 2 * sizeof(ULONG))
        {
            PEPROCESS process;
            PETHREAD thread;
            CONTEXT context = {0};
            status = PsLookupProcessByProcessId((HANDLE)(ULONG_PTR)*(ULONG *)irp->AssociatedIrp.SystemBuffer, &process);
            if (!status)
            {
                if (held_process) ObDereferenceObject(held_process);
                held_process = process;
                status = PsLookupThreadByThreadId((HANDLE)(ULONG_PTR)((ULONG *)irp->AssociatedIrp.SystemBuffer)[1], &thread);
                if (!status)
                {
                    context.ContextFlags = CONTEXT_CONTROL;
                    status = PsGetContextThread(thread, &context, UserMode);
                    ObDereferenceObject(thread);
                    DbgPrint("NIKKE_CONTEXT_PROBE captured=%u status=%08x\n", !status && context.Rip && context.Rsp, status);
                    if (!status && (!context.Rip || !context.Rsp)) status = STATUS_UNSUCCESSFUL;
                }
            }
        }
        else if (code != IOCTL_STATUS) status = STATUS_INVALID_DEVICE_REQUEST;
        if (!status && !held_process) status = STATUS_INVALID_DEVICE_STATE;
        if (!status)
        {
            *(NTSTATUS *)irp->AssociatedIrp.SystemBuffer = PsGetProcessExitStatus(held_process);
            length = sizeof(NTSTATUS);
        }
    }
    irp->IoStatus.Status = status;
    irp->IoStatus.Information = length;
    IoCompleteRequest(irp, IO_NO_INCREMENT);
    return status;
}

static void NTAPI unload(DRIVER_OBJECT *driver)
{
    if (held_process) ObDereferenceObject(held_process);
    IoDeleteSymbolicLink(&link_name);
    IoDeleteDevice(driver->DeviceObject);
}

NTSTATUS NTAPI DriverEntry(DRIVER_OBJECT *driver, UNICODE_STRING *path)
{
    UNICODE_STRING device_name;
    DEVICE_OBJECT *device;
    NTSTATUS status;
    unsigned int i;
    (void)path;
    RtlInitUnicodeString(&device_name, L"\\Device\\NIKKE-Status-Probe");
    RtlInitUnicodeString(&link_name, L"\\DosDevices\\NIKKE-Status-Probe");
    status = IoCreateDevice(driver, 0, &device_name, FILE_DEVICE_UNKNOWN, 0, FALSE, &device);
    if (status) return status;
    status = IoCreateSymbolicLink(&link_name, &device_name);
    if (status) { IoDeleteDevice(device); return status; }
    for (i = 0; i <= IRP_MJ_MAXIMUM_FUNCTION; ++i) driver->MajorFunction[i] = dispatch;
    driver->DriverUnload = unload;
    device->Flags &= ~DO_DEVICE_INITIALIZING;
    return STATUS_SUCCESS;
}
