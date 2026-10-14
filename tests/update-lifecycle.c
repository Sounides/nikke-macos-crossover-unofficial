/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Owned file-replacement/restart fixture. No vendor code or updater protocol.
 * Official basenames exercise this runtime's image-specific configuration.
 */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#define LAUNCHER L"C:\\NIKKE\\Launcher\\nikke_launcher.exe"
#define GAME L"C:\\NIKKE\\NIKKE\\game\\nikke.exe"

static int fail(const char *step)
{
    FILE *file = fopen("C:\\NIKKE\\Launcher\\fixture-failed.txt", "w");
    if (file) { fprintf(file, "%s error=%lu\n", step, GetLastError()); fclose(file); }
    return 1;
}

static int settings_preserved(void)
{
    HKEY key;
    DWORD value = 0, size = sizeof(value), type = 0;
    WCHAR setting[32];
    if (!GetEnvironmentVariableW(L"NIKKE_UPDATE_TEST_SENTINEL", setting, 32) ||
        wcscmp(setting, L"owned-fixture")) return 0;
    if (RegOpenKeyExW(HKEY_CURRENT_USER, L"Software\\Wine\\AppDefaults\\nikke.exe\\Direct3D",
                      0, KEY_READ, &key)) return 0;
    LONG status = RegQueryValueExW(key, L"no_create_flags", NULL, &type, (BYTE *)&value, &size);
    RegCloseKey(key);
    if (status || type != REG_DWORD || value != 0x800) return 0;
    if (RegOpenKeyExW(HKEY_CURRENT_USER, L"Software\\Wine\\AppDefaults\\nikke.exe\\DllOverrides",
                      0, KEY_READ, &key)) return 0;
    size = sizeof(setting);
    status = RegQueryValueExW(key, L"d3d11", NULL, &type, (BYTE *)setting, &size);
    RegCloseKey(key);
    return !status && type == REG_SZ && !wcscmp(setting, L"b");
}

static int start(const WCHAR *image, const WCHAR *arguments, PROCESS_INFORMATION *process)
{
    WCHAR command[1024];
    STARTUPINFOW startup = { sizeof(startup) };
    /* A different working directory catches accidental relative-path reliance. */
    swprintf(command, 1024, L"\"%ls\" %ls", image, arguments);
    memset(process, 0, sizeof(*process));
    return CreateProcessW(image, command, NULL, NULL, FALSE, CREATE_NO_WINDOW,
                          NULL, L"C:\\windows\\temp", &startup, process);
}

static int update(DWORD parent_id)
{
    HANDLE parent = OpenProcess(SYNCHRONIZE, FALSE, parent_id);
    if (parent)
    {
        DWORD wait = WaitForSingleObject(parent, 15000);
        CloseHandle(parent);
        if (wait != WAIT_OBJECT_0) return fail("wait for old launcher");
    }
    else if (GetLastError() != ERROR_INVALID_PARAMETER)
        return fail("open old launcher");

    /* Model the helper's replace-then-relaunch sequence after the parent exits. */
    if (!MoveFileExW(LAUNCHER, LAUNCHER L".old", MOVEFILE_WRITE_THROUGH) ||
        !MoveFileExW(LAUNCHER L".pending", LAUNCHER, MOVEFILE_WRITE_THROUGH) ||
        !MoveFileExW(GAME, GAME L".old", MOVEFILE_WRITE_THROUGH) ||
        !MoveFileExW(GAME L".pending", GAME, MOVEFILE_WRITE_THROUGH))
        return fail("replace owned executable files");
    PROCESS_INFORMATION process;
    if (!start(LAUNCHER, L"--after-update", &process)) return fail("restart launcher");
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return 0;
}

int wmain(int argc, WCHAR **argv)
{
    if (argc == 3 && !wcscmp(argv[1], L"--update"))
        return update(wcstoul(argv[2], NULL, 10));

#if defined(FIXTURE_GAME)
    if (FIXTURE_VERSION != 2 || !settings_preserved()) return fail("updated game settings");
    FILE *file = fopen("C:\\NIKKE\\Launcher\\game-v2.ok", "w");
    if (!file) return fail("write game result");
    fputs("owned-game-v2\n", file); fclose(file);
    return 0;
#elif FIXTURE_VERSION == 1
    WCHAR arguments[80];
    PROCESS_INFORMATION process;
    if (!settings_preserved()) return fail("initial launcher settings");
    swprintf(arguments, 80, L"--update %lu", GetCurrentProcessId());
    if (!start(L"C:\\NIKKE\\Launcher\\startup_runner.exe", arguments, &process))
        return fail("start update helper");
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return 0;
#else
    PROCESS_INFORMATION process;
    DWORD exit_code = 1;
    if (argc != 2 || wcscmp(argv[1], L"--after-update") || !settings_preserved())
        return fail("updated launcher arguments/settings");
    if (!start(GAME, L"--owned-fixture", &process)) return fail("launch updated game");
    CloseHandle(process.hThread);
    DWORD wait = WaitForSingleObject(process.hProcess, 30000);
    GetExitCodeProcess(process.hProcess, &exit_code);
    CloseHandle(process.hProcess);
    if (wait != WAIT_OBJECT_0 || exit_code) return fail("updated game completion");
    FILE *file = fopen("C:\\NIKKE\\Launcher\\launcher-v2.ok", "w");
    if (!file) return fail("write launcher result");
    fputs("owned-launcher-v2\n", file); fclose(file);
    return 0;
#endif
}
