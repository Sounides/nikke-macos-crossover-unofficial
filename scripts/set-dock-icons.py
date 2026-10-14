#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Use one locally supplied ICNS for the launcher and game Wine bundles."""
import argparse
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-root', required=True, type=Path)
parser.add_argument('--icon', required=True, type=Path, help='Local ICNS from the generated app\'s Contents/Resources/NIKKE.icns')
args = parser.parse_args()
root = args.work_root.resolve()
icon = args.icon.expanduser().resolve()
if not icon.is_file() or icon.read_bytes()[:4] != b'icns':
    parser.error('Provide a valid local ICNS file')
unix = root/'runtime/lib/wine/x86_64-unix'
bundles = [(unix/'NIKKE Launcher.app', 'Unofficial Launcher for NIKKE'),
           (unix/'NIKKE.app', 'Unofficial NIKKE Game Host')]
for bundle, name in bundles:
    if not (bundle/'Contents/Info.plist').is_file():
        parser.error('Prepare the Wine app bundles first')
checkpoint = root/'checkpoints'/('dock-icons-'+str(time.time_ns()))
for bundle, name in bundles:
    info_path = bundle/'Contents/Info.plist'
    old_icon = bundle/'Contents/Resources/NIKKE.icns'
    backup = checkpoint/bundle.name
    backup.mkdir(parents=True)
    shutil.copy2(info_path, backup/'Info.plist')
    if old_icon.is_file(): shutil.copy2(old_icon, backup/'NIKKE.icns')
    old_icon.parent.mkdir(parents=True, exist_ok=True)
    if icon != old_icon.resolve(): shutil.copy2(icon, old_icon)
    info = plistlib.loads(info_path.read_bytes())
    info.update(CFBundleIconFile='NIKKE', CFBundleName=name, CFBundleDisplayName=name,
                CFBundleVersion='11.18.1', WineUseBundleIcon=True)
    info_path.write_bytes(plistlib.dumps(info))
    # Signing may rewrite the loader header. Preserve the inode mapped by an
    # already running process, so its image is never changed underneath it.
    loader = bundle/'Contents/MacOS/wine'
    replacement = loader.with_name('wine.icon-new')
    shutil.copy2(loader, replacement)
    os.replace(replacement, loader)
    subprocess.run(['codesign', '--force', '--sign', '-', str(bundle)], check=True)
    # Wine's loader deliberately links ntdll.so outside the small UI bundle.
    # Verify its signature without the standalone-bundle relocation restriction.
    subprocess.run(['codesign', '--verify', str(bundle)], check=True)
    bundle.touch()
    print('Updated', name)
print('Close and reopen the launcher/game to refresh their running Dock icons.')
