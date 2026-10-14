#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Package this isolated Wine build for macOS app selection."""
import argparse
from pathlib import Path
import plistlib
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--work-root', required=True, type=Path)
args = parser.parse_args()
unix = args.work_root.resolve() / 'runtime/lib/wine/x86_64-unix'
# Internal folder names and identifiers remain stable for loader routing.
# Only our generated macOS hosts receive these labels; vendor files are untouched.
for name, display_name, identifier, helper in (
    ('NIKKE Launcher', 'Unofficial Launcher for NIKKE', 'org.winehq.wine', False),
    ('Wine Helpers', 'Wine Helpers', 'org.winehq.nikke.helpers', True),
    ('NIKKE', 'Unofficial NIKKE Game Host', 'org.winehq.nikke.unityprobe', False),
):
    app = unix / (name + '.app')
    executable = app / 'Contents/MacOS/wine'
    executable.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(unix / 'wine', executable)
    link = executable.parent / 'ntdll.so'
    if link.is_symlink():
        if link.readlink() != Path('../../../ntdll.so'):
            raise RuntimeError(f'Unexpected existing link: {link}')
    elif link.exists():
        raise RuntimeError(f'Unexpected existing file: {link}')
    else:
        link.symlink_to('../../../ntdll.so')
    info = dict(CFBundleExecutable='wine', CFBundleIdentifier=identifier,
                CFBundleName=display_name, CFBundleDisplayName=display_name, CFBundlePackageType='APPL',
                CFBundleVersion='11.18', LSUIElement=helper,
                NSPrincipalClass='WineApplication')
    if name == 'NIKKE':
        info.update(LSSupportsGameMode=True, LSApplicationCategoryType='public.app-category.games')
    if (app/'Contents/Resources/NIKKE.icns').is_file():
        info.update(CFBundleIconFile='NIKKE', CFBundleVersion='11.18.1', WineUseBundleIcon=True)
    (app / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
    subprocess.run(['codesign', '--force', '--sign', '-', str(app)], check=True)

    register = Path('/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister')
    if register.is_file():
        subprocess.run([str(register), '-f', str(app)], check=True)
