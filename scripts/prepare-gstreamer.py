#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
import argparse
from pathlib import Path
import shutil, subprocess, sys, xml.etree.ElementTree as ET
parser = argparse.ArgumentParser()
parser.add_argument('--work-root', required=True, type=Path)
parser.add_argument('packages', nargs='+')
args = parser.parse_args()
root = args.work_root.resolve()
framework = root / 'runtime/Frameworks/GStreamer.framework'
old = '/Library/Frameworks/GStreamer.framework'
for package_root in args.packages:
    for info in Path(package_root).glob('*.pkg/PackageInfo'):
        location = ET.parse(info).getroot().get('install-location', '')
        if not location.rstrip('/').startswith(old):
            continue
        payload = info.parent / 'Payload'
        if not payload.exists():
            continue
        dest = framework / location[len(old):].lstrip('/')
        for source in payload.rglob('*'):
            target = dest / source.relative_to(payload)
            if source.is_symlink():
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.is_symlink() and target.readlink() == source.readlink():
                    continue
                if target.exists() or target.is_symlink():
                    target.unlink()
                target.symlink_to(source.readlink())
            elif source.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
print('Framework packages copied into isolated runtime')
# Rewrite dependencies relative to each file, avoiding global framework installation.
import os
count = 0
magic = {b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf'}
for binary in framework.rglob('*'):
    if binary.is_symlink() or not binary.is_file() or binary.suffix in ('.a', '.o'):
        continue
    with binary.open('rb') as f:
        if f.read(4) not in magic:
            continue
    dependencies = subprocess.check_output(['/usr/bin/otool', '-L', str(binary)], text=True)
    changes = set()
    for line in dependencies.splitlines():
        dep = line.strip().split(' (compatibility version')[0]
        if dep.startswith(old + '/'):
            new = '@loader_path/' + os.path.relpath(framework / dep[len(old):].lstrip('/'), binary.parent)
            changes.add((dep, new))
    args = ['/usr/bin/install_name_tool']
    for dep, new in sorted(changes):
        args += ['-change', dep, new]
    if binary.suffix == '.dylib':
        args += ['-id', '@rpath/' + binary.name]
    if len(args) > 1:
        subprocess.run(args + [str(binary)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        subprocess.run(['/usr/bin/codesign', '--force', '--sign', '-', str(binary)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    count += 1
print('Isolated Mach-O files prepared:', count)

# Use only the plugins needed by the game and Wine's video parser.
plugin_dir = framework / 'Versions/1.0/lib/gstreamer-nikke'
plugin_dir.mkdir(exist_ok=True)
for name in ('coreelements', 'typefindfunctions', 'isomp4', 'videoparsersbad', 'playback', 'app',
             'audioconvert', 'audioresample', 'audioparsers', 'libav', 'videoconvertscale',
             'deinterlace', 'videofilter'):
    filename = 'libgst' + name + '.dylib'
    shutil.copy2(framework / 'Versions/1.0/lib/gstreamer-1.0' / filename, plugin_dir / filename)
print('NIKKE media plugin set prepared: 13 plugins')
