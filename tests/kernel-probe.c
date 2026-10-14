/* SPDX-License-Identifier: LGPL-2.1-or-later */
#include <ddk/ntddk.h>

static void NTAPI unload(DRIVER_OBJECT *object) { (void)object; }

NTSTATUS NTAPI DriverEntry(DRIVER_OBJECT *object, UNICODE_STRING *path)
{
    static const WCHAR expected_name[] = L"NIKKE-Compat-Probe";
    static const WCHAR expected_path[] = L"\\Registry\\Machine\\System\\CurrentControlSet\\Services\\NIKKE-Compat-Probe";
    ULONG_PTR address = (ULONG_PTR)__builtin_return_address(0);
    BOOLEAN tagged = (address & 0xffff800000000000ULL) == 0xffff800000000000ULL;
    BOOLEAN service_name = object->DriverExtension->ServiceKeyName.Length == sizeof(expected_name) - sizeof(WCHAR);
    BOOLEAN registry_path = path->Length == sizeof(expected_path) - sizeof(WCHAR);
    unsigned int i;
    object->DriverUnload = unload;
    for (i = 0; service_name && i < sizeof(expected_name) / sizeof(WCHAR) - 1; ++i)
        service_name = object->DriverExtension->ServiceKeyName.Buffer[i] == expected_name[i];
    for (i = 0; registry_path && i < sizeof(expected_path) / sizeof(WCHAR) - 1; ++i)
        registry_path = path->Buffer[i] == expected_path[i];
    DbgPrint("NIKKE_KERNEL_PROBE tagged=%u service_name=%u registry_path=%u\n", tagged, service_name, registry_path);
    return tagged && service_name && registry_path ? STATUS_SUCCESS : STATUS_INVALID_DEVICE_STATE;
}
