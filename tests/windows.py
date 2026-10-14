#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Check owned popup minimization/restoration and standard-DPI coordinates.

Creates a unique account-free prefix. Only the fixture's own windows are
operated; the native probe reads geometry for that fixture PID alone.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-root', required=True, type=Path)
args = parser.parse_args()
root = args.work_root.resolve()
os.umask(0o077)
prefix = root/'window-test-prefix'/('run-'+str(time.time_ns()))
folder = prefix/'drive_c/window-fixture'
folder.mkdir(parents=True)
exe = prefix/'drive_c/NIKKE/Launcher/nikke_launcher.exe'
exe.parent.mkdir(parents=True)
sources = Path(__file__).resolve().parent
cc = root/'toolchain/llvm-mingw-20261006-ucrt-macos-universal/bin/i686-w64-mingw32-gcc'
wine, server = root/'runtime/bin/wine', root/'runtime/bin/wineserver'
probe = prefix/'window-state'
subprocess.run([str(cc), str(sources/'owned-windows.c'), '-o', str(exe), '-luser32', '-lgdi32'], check=True)
browser_images = ('intl_service.exe', 'tbs_browser.exe', 'INTLWebViewHelper.exe')
for name in browser_images:
    shutil.copy2(exe, folder/name)
subprocess.run(['xcrun', 'swiftc', '-O', str(sources/'window-state.swift'), '-o', str(probe)], check=True)
env = os.environ.copy()
for key in tuple(env):
    if key.startswith(('NIKKE_', 'WINE')):
        env.pop(key, None)
unix = root/'runtime/lib/wine/x86_64-unix'
env.update(WINEPREFIX=str(prefix), WINESERVER=str(server), WINEDEBUG='-all,err+all',
           WINEDLLOVERRIDES='mscoree,mshtml=', NIKKE_WINDOW_DIAGNOSTICS='1',
           NIKKE_WINE_APP_LOADER=str(unix/'NIKKE Launcher.app/Contents/MacOS/wine'),
           NIKKE_WINE_APP_TARGET='nikke_launcher.exe',
           NIKKE_WINE_HELPER_LOADER=str(unix/'Wine Helpers.app/Contents/MacOS/wine'))
log = prefix/'window-regression.log'

with log.open('wb') as output:
    def run(*arguments):
        subprocess.run([str(wine), *arguments], env=env, stdout=output,
                       stderr=subprocess.STDOUT, check=True, timeout=60)

    def stop():
        subprocess.run([str(server), '-k'], env=env, stdout=output, stderr=subprocess.STDOUT, timeout=30)
        subprocess.run([str(server), '-w'], env=env, stdout=output,
                       stderr=subprocess.STDOUT, check=True, timeout=30)

    def wait_phase(expected):
        deadline = time.monotonic()+30
        while time.monotonic() < deadline:
            if (folder/'phase.txt').exists() and (folder/'phase.txt').read_text() == expected:
                return
            time.sleep(0.1)
        raise RuntimeError('Owned window fixture timed out; inspect its private log')

    process = None
    try:
        run('wineboot.exe', '-u')
        run('reg.exe', 'add', r'HKCU\Control Panel\Desktop', '/v', 'LogPixels', '/t', 'REG_DWORD', '/d', '192', '/f')
        run('reg.exe', 'add', r'HKCU\Software\Wine\Mac Driver', '/v', 'RetinaMode', '/t', 'REG_SZ', '/d', 'Y', '/f')
        for name in ('nikke_launcher.exe', *browser_images):
            key = 'HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\'+name
            run('reg.exe', 'add', key, '/v', 'dpiAwareness', '/t', 'REG_DWORD', '/d', '0', '/f')
        stop()
        for name in browser_images:
            (folder/'dpi-probe.txt').unlink(missing_ok=True)
            run(str(folder/name), '--dpi-probe')
            assert (folder/'dpi-probe.txt').read_text().strip() == 'dpi=96 awareness=0'
        process = subprocess.Popen([str(wine), str(exe)], env=env, stdout=output, stderr=subprocess.STDOUT)
        wait_phase('normal')
        text = log.read_text(errors='replace')
        match = re.search(r'NIKKE-WINDOW[^\n]* pid=(\d+) bundle=org\.winehq\.wine ', text)
        if not match:
            raise RuntimeError('The owned fixture did not use the selected native launcher host')
        pid = match.group(1)

        def windows():
            result = subprocess.run([str(probe), pid], capture_output=True, text=True, check=True, timeout=15)
            return [w for w in json.loads(result.stdout) if w['layer'] == 0]

        def wait_count(expected):
            deadline = time.monotonic()+10
            while time.monotonic() < deadline:
                found = windows()
                if len(found) == expected:
                    return found
                time.sleep(0.1)
            raise RuntimeError('Native window visibility differs from the expected state')

        # Native ordering and frame changes are asynchronous. Wait for both
        # visibility and geometry, rather than sampling the first ordered frame.
        deadline = time.monotonic()+10
        while time.monotonic() < deadline:
            normal = wait_count(5)
            main = next(w for w in normal if w['bounds']['Width'] > 100 and w['bounds']['Height'] > 100)
            if main['bounds']['Width'] == 600 and main['bounds']['Height'] == 360:
                break
            time.sleep(0.1)
        else:
            raise RuntimeError('Owned client did not reach 600x360 native points: '+str(main['bounds']))
        assert 'normal dpi=96 awareness=0 client=600x360' in text
        (folder/'command.txt').write_text('1')
        wait_phase('minimized')
        wait_count(0)
        (folder/'command.txt').write_text('2')
        wait_phase('restored')
        wait_count(4)  # root and three shadows; one was explicitly hidden while minimized
        (folder/'command.txt').write_text('3')
        if process.wait(timeout=15) != 0:
            raise RuntimeError('Owned fixture failed')
    finally:
        if process and process.poll() is None:
            process.terminate()
        stop()
print('PASS: standard-DPI client maps to the expected point size; all owned shadows hide on minimize.')
print('PASS: restore shows only the root and still-visible popups; account prefix was not used.')
print('PASS: three owned browser-helper images retain standard DPI despite requesting DPI awareness.')
