/* SPDX-License-Identifier: LGPL-2.1-or-later */
#include <windows.h>
#include <stdio.h>
#define IOCTL_HOLD CTL_CODE(FILE_DEVICE_UNKNOWN, 0x800, METHOD_BUFFERED, FILE_ANY_ACCESS)
#define IOCTL_STATUS CTL_CODE(FILE_DEVICE_UNKNOWN, 0x801, METHOD_BUFFERED, FILE_ANY_ACCESS)

int main(int argc, char **argv)
{
    HANDLE event, device;
    PROCESS_INFORMATION child;
    STARTUPINFOA startup = {sizeof(startup)};
    char executable[MAX_PATH], command[MAX_PATH + 16];
    DWORD returned, live = 0, exited = 0, child_exit = 0;
    DWORD ids[2];
    BOOL ok;
    event = CreateEventW(NULL, TRUE, FALSE, L"NIKKE-Status-Test-Exit");
    if (!event) return 1;
    if (argc > 1)
    {
        DWORD wait = WaitForSingleObject(event, 30000);
        CloseHandle(event);
        return wait == WAIT_OBJECT_0 ? 0x1234 : 1;
    }
    device = CreateFileW(L"\\\\.\\NIKKE-Status-Probe", GENERIC_READ | GENERIC_WRITE, 0,
                         NULL, OPEN_EXISTING, 0, NULL);
    if (device == INVALID_HANDLE_VALUE) { printf("device error=%lu\n", GetLastError()); return 2; }
    GetModuleFileNameA(NULL, executable, sizeof(executable));
    snprintf(command, sizeof(command), "\"%s\" child", executable);
    if (!CreateProcessA(executable, command, NULL, NULL, FALSE, 0, NULL, NULL, &startup, &child)) return 3;
    ids[0] = child.dwProcessId; ids[1] = child.dwThreadId;
    SuspendThread(child.hThread);
    ok = DeviceIoControl(device, IOCTL_HOLD, ids, sizeof(ids),
                         &live, sizeof(live), &returned, NULL);
    ResumeThread(child.hThread);
    SetEvent(event);
    if (WaitForSingleObject(child.hProcess, 30000) != WAIT_OBJECT_0) TerminateProcess(child.hProcess, 1);
    GetExitCodeProcess(child.hProcess, &child_exit);
    ok = ok && DeviceIoControl(device, IOCTL_STATUS, NULL, 0, &exited, sizeof(exited), &returned, NULL);
    printf("PROCESS_STATUS_PROBE live=%08lx exited=%08lx actual_child_exit=%08lx ioctl_ok=%d\n",
           live, exited, child_exit, ok);
    CloseHandle(child.hThread); CloseHandle(child.hProcess);
    CloseHandle(device); CloseHandle(event);
    return ok && live == 0x103 && exited == 0x1234 && child_exit == 0x1234 ? 0 : 4;
}
