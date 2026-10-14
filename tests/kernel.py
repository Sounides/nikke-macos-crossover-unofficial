#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Run owned kernel/API fixtures in a separate account-free Wine prefix."""
import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-root', required=True, type=Path)
args = parser.parse_args()
root = args.work_root.resolve()
sources = Path(__file__).resolve().parent
test_root = root/'kernel-test-prefix'
if (test_root/'drive_c/NIKKE').exists():
    parser.error('The regression prefix must not contain an official game installation')
prefix = test_root/('run-'+str(time.time_ns()))
os.umask(0o077)
fixtures = prefix/'drive_c/fixtures'
fixtures.mkdir(parents=True, exist_ok=True)
logs = root/'logs'
logs.mkdir(exist_ok=True)
log = logs/'kernel-regression.log'
toolchain = root/'toolchain/llvm-mingw-20261006-ucrt-macos-universal/bin'
compiler = toolchain/'x86_64-w64-mingw32-gcc'
wine = root/'runtime/bin/wine'
server = root/'runtime/bin/wineserver'
env = os.environ.copy()
env.update(WINEPREFIX=str(prefix), WINESERVER=str(server),
           WINEDEBUG='-all,err+all,+debugstr', WINEDLLOVERRIDES='mscoree,mshtml=')
for key in ('NIKKE_DXMT', 'NIKKE_D3DMETAL', 'NIKKE_WINE_APP_LOADER',
            'NIKKE_WINE_GAME_APP_LOADER', 'NIKKE_WINE_HELPER_LOADER',
            'NIKKE_METAL_METRICS_FILE', 'NIKKE_CEF_SOFTWARE'):
    env.pop(key, None)

def compile_fixture(name, *, driver=False, unicode=False, bits=64):
    cc = compiler if bits == 64 else toolchain/'i686-w64-mingw32-gcc'
    target = fixtures/(name+('32' if bits == 32 else '')+('.sys' if driver else '.exe'))
    flags = ['-I'+str(toolchain.parent/'x86_64-w64-mingw32/include/ddk'),
             '-shared', '-nostdlib', '-Wl,--subsystem,native',
             '-Wl,--entry,DriverEntry', '-lntoskrnl'] if driver else []
    if unicode:
        flags.append('-municode')
    subprocess.run([str(cc), str(sources/(name+'.c')), '-o', str(target), *flags], check=True)
    return target

for name in ('kernel-probe', 'kernel-thread-probe', 'ex-work-item-probe', 'process-status-driver'):
    compile_fixture(name, driver=True)
for name in ('process-status-client', 'mdl-mapping', 'thread-context', 'nop-probe'):
    compile_fixture(name)
compile_fixture('nop-probe', bits=32)
cef = compile_fixture('cef-switches', unicode=True)
for name in ('intl_service.exe', 'unrelated.exe'):
    shutil.copy2(cef, fixtures/name)
for name in ('kernel-thread-result.bin', 'ex-work-item-result.bin'):
    (fixtures/name).unlink(missing_ok=True)

with log.open('wb') as output:
    def run(*arguments, expected=0):
        result = subprocess.run([str(wine), *map(str, arguments)], env=env,
                                stdout=output, stderr=subprocess.STDOUT, timeout=60)
        if expected is not None and result.returncode != expected:
            raise RuntimeError('Owned fixture failed; review the private kernel-regression.log')

    def service(name, image, client=None):
        run('sc.exe', 'create', name, 'type=', 'kernel', 'start=', 'demand',
            'binPath=', 'C:\\fixtures\\'+image+'.sys')
        try:
            run('sc.exe', 'start', name)
            if client:
                run(fixtures/(client+'.exe'))
        finally:
            run('sc.exe', 'stop', name, expected=None)
            run('sc.exe', 'delete', name, expected=None)

    try:
        run('wineboot.exe', '-u')
        run(fixtures/'mdl-mapping.exe')
        run(fixtures/'thread-context.exe')
        run(cef)
        for bits in ('', '32'):
            for mode in ('register', 'memory', 'ud2', 'lock'):
                run(fixtures/('nop-probe'+bits+'.exe'), mode,
                    expected=0 if mode in ('register', 'memory') else 2)
        service('NIKKE-Compat-Probe', 'kernel-probe')
        service('NIKKE-Kernel-Thread-Probe', 'kernel-thread-probe')
        service('NIKKE-Work-Item-Probe', 'ex-work-item-probe')
        service('NIKKE-Status-Probe', 'process-status-driver', 'process-status-client')
    finally:
        subprocess.run([str(server), '-k'], env=env, stdout=output, stderr=subprocess.STDOUT, timeout=30)
        subprocess.run([str(server), '-w'], env=env, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=30)

text = log.read_text(errors='replace')
assert 'PASS: shared contents, interior addresses, two MDL references, deferred release' in text
assert 'user_status=00000000 registers_match=1' in text
assert 'CEF_SWITCHES checks=7 passed=7' in text
assert 'NIKKE_KERNEL_PROBE tagged=1 service_name=1 registry_path=1' in text
assert 'live=00000103 exited=00001234 actual_child_exit=00001234 ioctl_ok=1' in text
assert 'NIKKE_CONTEXT_PROBE captured=1 status=00000000' in text
assert struct.unpack('<III', (fixtures/'kernel-thread-result.bin').read_bytes()) == (0, 1, 1)
assert struct.unpack('<8I', (fixtures/'ex-work-item-result.bin').read_bytes()) == (1,)*8
print('PASS: allocation-wide MDLs, scoped CEF switches (7), thread context, NOPs (8),')
print('      driver/service identity, kernel thread, System work items and process exit status.')
print('Only kernel-test-prefix was used. Fixture logs remain private in the work root.')
