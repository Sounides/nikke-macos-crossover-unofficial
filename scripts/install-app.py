#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Build a native starter for an existing setup; no runtime or account is copied."""
import argparse
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-root', required=True, type=Path)
parser.add_argument('--destination', type=Path, default=Path('/Applications/Unofficial Launcher for NIKKE.app'))
parser.add_argument('--icon', type=Path, help='User-supplied PNG or JPEG game icon; stored only in the generated app')
args = parser.parse_args()
root = args.work_root.resolve()
if not (root / 'runtime/bin/wine').is_file():
    parser.error('The selected work root must contain runtime/bin/wine')
if args.icon and not args.icon.expanduser().is_file():
    parser.error('The supplied icon file does not exist')
dest = args.destination.expanduser().absolute()
if dest.exists():
    parser.error('Destination already exists; choose a new destination or move the existing app aside.')
dest.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='nikke-app-', dir=dest.parent) as tmp:
    stage = Path(tmp) / 'Unofficial Launcher for NIKKE.app'
    macos, resources = stage / 'Contents/MacOS', stage / 'Contents/Resources'
    macos.mkdir(parents=True); resources.mkdir()
    subprocess.run(['xcrun', 'swiftc', '-O', '-framework', 'AppKit', str(repo/'app/NIKKE.swift'), '-o', str(macos/'NIKKE')], check=True)
    icon_png = Path(tmp) / 'icon.png'
    if args.icon:
        subprocess.run(['sips', '-s', 'format', 'png', str(args.icon.expanduser().resolve()), '--out', str(icon_png)], check=True, stdout=subprocess.DEVNULL)
    else:
        icon_builder = Path(tmp) / 'icon-builder'
        subprocess.run(['xcrun', 'swiftc', '-O', '-framework', 'AppKit', str(repo/'app/Icon.swift'), '-o', str(icon_builder)], check=True)
        subprocess.run([str(icon_builder), str(icon_png)], check=True)
    iconset = Path(tmp) / 'NIKKE.iconset'; iconset.mkdir()
    for size in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            name = f'icon_{size}x{size}' + ('@2x' if scale == 2 else '') + '.png'
            subprocess.run(['sips', '-z', str(size*scale), str(size*scale), str(icon_png), '--out', str(iconset/name)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['iconutil', '-c', 'icns', str(iconset), '-o', str(resources/'NIKKE.icns')], check=True)
    shutil.copy2(repo/'scripts/run.sh', resources/'run.sh')
    (resources/'Setup.plist').write_bytes(plistlib.dumps({'WorkRoot': str(root)}))
    info = dict(CFBundleExecutable='NIKKE', CFBundleIdentifier='local.nikke-compat.unofficial-launcher',
                CFBundleName='Unofficial Launcher for NIKKE',
                CFBundleDisplayName='Unofficial Launcher for NIKKE', CFBundlePackageType='APPL',
                CFBundleIconFile='NIKKE', CFBundleVersion='1', CFBundleShortVersionString='1.0',
                LSMinimumSystemVersion='13.0', LSUIElement=True, NSHighResolutionCapable=True)
    (stage/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
    subprocess.run(['codesign', '--force', '--sign', '-', str(stage)], check=True)
    stage.rename(dest)
subprocess.run(['python3', str(repo/'scripts/set-dock-icons.py'), '--work-root', str(root),
                '--icon', str(dest/'Contents/Resources/NIKKE.icns')], check=True)
print('Installed', dest)
