#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Exercise owned updater replacement/restart in a unique account-free prefix.

This does not download a vendor update, copy an account, or test a future
launcher/CEF/ACE version. The runtime is reused without changing its files.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-root', required=True, type=Path)
args = parser.parse_args()
root = args.work_root.resolve()
runtime = root/'runtime'
wine, server = runtime/'bin/wine', runtime/'bin/wineserver'
toolchain = root/'toolchain/llvm-mingw-20261006-ucrt-macos-universal/bin'
for path in (wine, server, toolchain/'i686-w64-mingw32-gcc', toolchain/'x86_64-w64-mingw32-gcc'):
    if not path.is_file():
        parser.error('Build the runtime and prepare the pinned toolchain first')
os.umask(0o077)
test = root/'update-tests'/('run-'+str(time.time_ns()))
test.mkdir(parents=True)
# run.sh expects this layout; the only runtime link points at the caller's
# existing runtime. No bundle preparation or runtime-writing script is called.
(test/'runtime').symlink_to(runtime, target_is_directory=True)
prefix = test/'custom-prefix'
launcher = prefix/'drive_c/NIKKE/Launcher'
game = prefix/'drive_c/NIKKE/NIKKE/game'
launcher.mkdir(parents=True); game.mkdir(parents=True)
(test/'dxmt-enabled').write_text('owned update lifecycle fixture\n')
source = Path(__file__).with_name('update-lifecycle.c')
repo = source.parent.parent
log = test/'fixture.log'
env = os.environ.copy()
for key in tuple(env):
    if key.startswith(('NIKKE_', 'WINE')) or key in ('DXMT_CONFIG', 'DXMT_SHADER_CACHE_PATH'):
        env.pop(key, None)
env.update(WINEPREFIX=str(prefix), WINESERVER=str(server), WINEDEBUG='-all,err+all',
           WINEDLLOVERRIDES='mscoree,mshtml=', NIKKE_UPDATE_TEST_SENTINEL='owned-fixture')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for bits, version, target, flags in (
    (32, 1, launcher/'nikke_launcher.exe', []),
    (32, 2, launcher/'nikke_launcher.exe.pending', []),
    (64, 1, game/'nikke.exe', ['-DFIXTURE_GAME']),
    (64, 2, game/'nikke.exe.pending', ['-DFIXTURE_GAME']),
):
    cc = toolchain/('i686-w64-mingw32-gcc' if bits == 32 else 'x86_64-w64-mingw32-gcc')
    subprocess.run([str(cc), '-municode', '-DFIXTURE_VERSION='+str(version), *flags,
                    str(source), '-o', str(target), '-ladvapi32'], check=True)
shutil.copy2(launcher/'nikke_launcher.exe', launcher/'startup_runner.exe')
expected = {path: digest(path.with_name(path.name+'.pending'))
            for path in (launcher/'nikke_launcher.exe', game/'nikke.exe')}
retained = {launcher/'client-settings.keep': b'owned launcher preference\n',
            game/'client-settings.keep': b'owned game preference\n'}
for path, data in retained.items():
    path.write_bytes(data)
runtime_before = {path: digest(path) for path in (wine, server,
    runtime/'lib/wine/i386-windows/kernelbase.dll',
    runtime/'lib/wine/x86_64-windows/kernelbase.dll')}

with log.open('wb') as output:
    def run(*arguments):
        subprocess.run([str(wine), *map(str, arguments)], env=env, stdout=output,
                       stderr=subprocess.STDOUT, check=True, timeout=60)

    try:
        run('wineboot.exe', '-u')
        run('reg.exe', 'add', 'HKCU\\Software\\Wine\\AppDefaults\\nikke.exe\\DllOverrides',
            '/v', 'd3d11', '/t', 'REG_SZ', '/d', 'b', '/f')
        subprocess.run(['/bin/bash', str(repo/'scripts/run.sh'), str(test), 'launch'],
                       env=env, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=60)
        deadline = time.monotonic()+60
        while not (launcher/'launcher-v2.ok').exists():
            if (launcher/'fixture-failed.txt').exists():
                raise RuntimeError('Owned updater failed; inspect the private fixture result')
            if time.monotonic() >= deadline:
                raise RuntimeError('Owned updater timed out; inspect the private fixture log')
            time.sleep(0.2)
        if (launcher/'game-v2.ok').read_text() != 'owned-game-v2\n':
            raise RuntimeError('Updated game did not report success')
        if (launcher/'launcher-v2.ok').read_text() != 'owned-launcher-v2\n':
            raise RuntimeError('Updated launcher did not report success')
        for path, value in expected.items():
            if digest(path) != value or not path.with_name(path.name+'.old').is_file():
                raise RuntimeError('Owned update bytes were not installed')
        for path, data in retained.items():
            if path.read_bytes() != data:
                raise RuntimeError('Owned preferences were not preserved')
        for path, value in runtime_before.items():
            if digest(path) != value:
                raise RuntimeError('Runtime unexpectedly changed')
    finally:
        subprocess.run([str(server), '-k'], env=env, stdout=output, stderr=subprocess.STDOUT, timeout=30)
        subprocess.run([str(server), '-w'], env=env, stdout=output,
                       stderr=subprocess.STDOUT, check=True, timeout=30)
print('PASS: owned 32-bit launcher/helper replacement and restart, then updated 64-bit game.')
print('PASS: inherited environment, video/DLL settings, preferences and sampled runtime hashes.')
print('No account or vendor files used; this is not an actual official-update compatibility test.')
