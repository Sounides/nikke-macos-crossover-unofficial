#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Install or restore a private DXMT backend in this isolated Wine setup."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-root', required=True, type=Path)
choice = parser.add_mutually_exclusive_group(required=True)
choice.add_argument('--donor', type=Path, help='DXMT directory from your own CrossOver installation')
choice.add_argument('--restore', type=Path, help='Checkpoint directory printed by a previous installation')
args = parser.parse_args()
root = args.work_root.resolve()
os.umask(0o077)
wine = root/'runtime/bin/wine'
server = root/'runtime/bin/wineserver'
system32 = root/'custom-prefix/drive_c/windows/system32'
if not wine.is_file() or not system32.is_dir():
    parser.error('Build Wine and initialize the isolated prefix first')
env = os.environ.copy()
env.update(WINEPREFIX=str(root/'custom-prefix'), WINEDEBUG='-all', WINEDLLOVERRIDES='mscoree,mshtml=')

def reg(*arguments, check=True):
    # Wine services may inherit stdout. A file avoids waiting for their pipe EOF.
    with tempfile.TemporaryFile() as capture:
        result = subprocess.run([str(wine), 'reg.exe', *arguments], env=env,
                                stdout=capture, stderr=subprocess.STDOUT, timeout=90)
        capture.seek(0)
        result.stdout = capture.read()
    if check and result.returncode:
        raise RuntimeError('Registry operation failed in the isolated prefix')
    return result

def local_path(relative):
    path = root/relative
    if not path.resolve().is_relative_to(root):
        raise RuntimeError('Checkpoint contains a path outside this work root')
    return path

def stop_prefix():
    # Wine's -k returns 1 when the server is already absent.
    result = subprocess.run([str(server), '-k'], env=env, timeout=90)
    if result.returncode not in (0, 1):
        raise RuntimeError('Could not stop the isolated Wine server')
    subprocess.run([str(server), '-w'], env=env, check=True, timeout=90)

def atomic_copy(source, target, native_copy=False):
    target.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray(source.read_bytes())
    # Prevent Wine from redirecting a renamed donor copy to its built-in DLL.
    if native_copy and data[64:80] == b'Wine builtin DLL':
        data[64:80] = b' '*16
    temporary = target.with_name(target.name+'.nikke-new')
    temporary.write_bytes(data)
    shutil.copymode(source, temporary)
    temporary.replace(target)

def restore(checkpoint):
    metadata = json.loads((checkpoint/'manifest.json').read_text())
    if metadata['work_root'] != str(root):
        raise RuntimeError('This checkpoint belongs to another work root')
    stop_prefix()
    for entry in metadata['files']:
        target = local_path(entry['target'])
        if entry['existed']:
            atomic_copy(checkpoint/entry['backup'], target)
        elif target.exists():
            target.unlink()
    for entry in metadata['registry']:
        if entry['value'] is None:
            reg('delete', entry['key'], '/v', entry['name'], '/f', check=False)
        else:
            reg('add', entry['key'], '/v', entry['name'], '/t', 'REG_SZ', '/d', entry['value'], '/f')
    stop_prefix()

if args.restore:
    checkpoint = args.restore.resolve()
    if not checkpoint.is_relative_to(root/'checkpoints'):
        parser.error('Use a DXMT checkpoint inside this work root')
    restore(checkpoint)
    print('Restored the prior graphics configuration. Checkpoint retained:', checkpoint)
else:
    donor = args.donor.resolve()
    names = ['x86_64-windows/d3d11.dll', 'x86_64-windows/dxgi.dll',
             'x86_64-windows/winemetal.dll', 'x86_64-unix/winemetal.so']
    for name in names:
        if not (donor/name).is_file():
            parser.error('Missing donor file: '+name)
    stop_prefix()
    checkpoint = root/'checkpoints'/('dxmt-'+str(time.time_ns()))
    checkpoint.mkdir(parents=True)
    copies = [(donor/names[0], system32/'nikke_dxmt.dll', True),
              (donor/names[1], system32/'dxgi.dll', True),
              (donor/names[2], root/'runtime/lib/wine/x86_64-windows/winemetal.dll', False),
              (donor/names[2], system32/'winemetal.dll', False),
              (donor/names[3], root/'runtime/lib/wine/x86_64-unix/winemetal.so', False)]
    changes = [(r'HKCU\Software\Wine\DllOverrides', 'd3d11', 'b'),
               (r'HKCU\Software\Wine\DllOverrides', 'dxgi', 'b')]
    key = r'HKCU\Software\Wine\AppDefaults\nikke.exe\DllOverrides'
    changes += [(key, 'd3d11', 'b'), (key, 'dxgi', 'n,b'),
                (key, 'winemetal', 'n,b'), (key, 'nikke_dxmt', 'n')]
    metadata = {'work_root': str(root), 'files': [], 'registry': [],
                'donor_checksums': {n: hashlib.sha256((donor/n).read_bytes()).hexdigest() for n in names}}
    # Back up every file and registry value before the first configuration change.
    for index, target in enumerate([item[1] for item in copies]+[root/'dxmt-enabled']):
        backup = str(index)
        exists = target.exists()
        if exists:
            shutil.copy2(target, checkpoint/backup)
        metadata['files'].append({'target': str(target.relative_to(root)), 'existed': exists, 'backup': backup})
    for key, name, value in changes:
        result = reg('query', key, '/v', name, check=False)
        text = result.stdout.decode(errors='replace')
        found = re.search(r'^\s*'+re.escape(name)+r'\s+REG_SZ\s+(.*?)\s*$', text, re.MULTILINE)
        if result.returncode == 0 and not found:
            raise RuntimeError('Existing override has an unsupported registry type')
        metadata['registry'].append({'key': key, 'name': name, 'value': found.group(1) if found else None})
    (checkpoint/'manifest.json').write_text(json.dumps(metadata, indent=2)+'\n')
    try:
        for source, target, native_copy in copies:
            atomic_copy(source, target, native_copy)
        for key, name, value in changes:
            reg('add', key, '/v', name, '/t', 'REG_SZ', '/d', value, '/f')
        (root/'dxmt-enabled').write_text('private DXMT donor installed\n')
        stop_prefix()
    except Exception:
        restore(checkpoint)
        raise
    print('Installed game-scoped DXMT. Rollback checkpoint:', checkpoint)
