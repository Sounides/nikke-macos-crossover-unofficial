/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Owned subprocess fixture. Its aliases belong only in kernel-test-prefix;
 * never replace the game's official verification service with this program. */
#include <windows.h>
#include <stdio.h>
#include <wchar.h>

static const WCHAR *options[] =
{ L"--disable-gpu", L"--disable-gpu-compositing", L"--in-process-gpu" };

static DWORD child_result(int argc, WCHAR **argv)
{
    unsigned i, j, count, mask = 0;
    for (i = 0; i < 3; ++i)
    {
        count = 0;
        for (j = 1; j < argc; ++j) count += !wcscmp(argv[j], options[i]);
        if (count > 1) return 8;
        if (count) mask |= 1u << i;
    }
    return mask;
}

static BOOL check_child(const WCHAR *base, const WCHAR *name, const WCHAR *flag,
                        const WCHAR *arguments, DWORD expected)
{
    WCHAR image[MAX_PATH], command[2048];
    STARTUPINFOW startup = { sizeof(startup) };
    PROCESS_INFORMATION process;
    DWORD code = 99;
    SetEnvironmentVariableW(L"NIKKE_CEF_SOFTWARE", flag);
    if (swprintf(image, MAX_PATH, L"%ls\\%ls", base, name) < 0 ||
        swprintf(command, 2048, L"\"%ls\" child %ls", image, arguments) < 0) return FALSE;
    if (!CreateProcessW(image, command, NULL, NULL, FALSE, 0, NULL, NULL, &startup, &process)) return FALSE;
    if (WaitForSingleObject(process.hProcess, 10000) == WAIT_OBJECT_0)
        GetExitCodeProcess(process.hProcess, &code);
    else TerminateProcess(process.hProcess, 99);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return code == expected;
}

int wmain(int argc, WCHAR **argv)
{
    WCHAR base[MAX_PATH], *slash;
    unsigned passed = 0;
    if (argc > 1 && !wcscmp(argv[1], L"child")) return child_result(argc, argv);
    if (!GetModuleFileNameW(NULL, base, MAX_PATH) || !(slash = wcsrchr(base, '\\'))) return 2;
    *slash = 0;
    passed += check_child(base, L"intl_service.exe", NULL, L"", 0);
    passed += check_child(base, L"intl_service.exe", L"1", L"", 7);
    passed += check_child(base, L"unrelated.exe", L"1", L"", 0);
    passed += check_child(base, L"intl_service.exe", L"1", L"--in-process-gpu", 7);
    passed += check_child(base, L"intl_service.exe", L"1", L"--disable-gpu-compositing", 7);
    passed += check_child(base, L"intl_service.exe", L"1",
                          L"--disable-gpu --disable-gpu-compositing --in-process-gpu", 7);
    passed += check_child(base, L"intl_service.exe", L"10", L"", 0);
    SetEnvironmentVariableW(L"NIKKE_CEF_SOFTWARE", NULL);
    printf("CEF_SWITCHES checks=7 passed=%u\n", passed);
    return passed == 7 ? 0 : 3;
}
