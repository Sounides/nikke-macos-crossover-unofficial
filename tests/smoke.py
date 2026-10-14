#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Run actual raw-syscall, device-flag and GPU-video checks in a prepared prefix."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-root', required=True, type=Path)
parser.add_argument('--video', required=True, type=Path, help='Your local H.264 MP4 with at least three changing nonblack frames')
parser.add_argument('--dxmt', action='store_true', help='Check the installed private DXMT route with these owned fixtures')
args = parser.parse_args()
root = args.work_root.resolve(); video = args.video.resolve()
if not video.is_file(): parser.error('The local video does not exist')
os.umask(0o077)
sources = Path(__file__).resolve().parent
compiler = root/'toolchain/llvm-mingw-20261006-ucrt-macos-universal/bin/x86_64-w64-mingw32-gcc'
fixtures = root/'fixtures'; fixtures.mkdir(exist_ok=True)
logs = root/'logs'; logs.mkdir(exist_ok=True)
env = os.environ.copy()
gst = root/'runtime/Frameworks/GStreamer.framework/Versions/1.0'
env.update(WINEPREFIX=str(root/'custom-prefix'), WINEDEBUG='-all', WINEDLLOVERRIDES='mscoree,mshtml=',
           GST_PLUGIN_SYSTEM_PATH_1_0=str(gst/'lib/gstreamer-nikke'), GST_PLUGIN_PATH_1_0='',
           GST_REGISTRY_1_0=str(root/'gst-registry-nikke-x86_64.bin'), GST_REGISTRY_FORK='no',
           GIO_MODULE_DIR=str(gst/'lib/gio/modules'))
wine = str(root/'runtime/bin/wine')

def run(name, *arguments):
    process_env = env.copy()
    if args.dxmt and name in ('video-flags', 'video-frames'):
        process_env.update(NIKKE_DXMT='1', NIKKE_DXMT_TARGET=name+'.exe',
                           WINEDLLOVERRIDES='d3d11=b;dxgi,winemetal,nikke_dxmt=n,b;mscoree,mshtml=')
    with tempfile.TemporaryFile() as capture:
        result = subprocess.run([wine, *map(str, arguments)], env=process_env, stdout=capture,
                                stderr=subprocess.STDOUT, timeout=90)
        capture.seek(0)
        text = capture.read().decode(errors='replace')
    (logs/('smoke-'+name+'.log')).write_text(text)
    if result.returncode: raise RuntimeError(name+' failed; review its local log')
    return text

def require(condition, name):
    if not condition: raise RuntimeError(name+' returned unexpected results; review its local log')
    print('PASS:', name, flush=True)

for name, libraries in [('raw-syscalls', []), ('video-flags', ['-ld3d11']),
                        ('video-frames', ['-municode','-ld3d11','-ldxgi','-lmfplat','-lmfreadwrite','-lmfuuid','-lole32','-luuid'])]:
    subprocess.run([str(compiler), str(sources/(name+'.c')), '-o', str(fixtures/(name+'.exe')), *libraries], check=True)

text = run('raw-syscalls', fixtures/'raw-syscalls.exe')
require('checks=4' in text and 'invalid_handle_status=c0000008' in text, 'raw Windows syscalls')
key = r'HKCU\Software\Wine\AppDefaults\video-flags.exe\Direct3D'
run('configure-video-flags', 'reg.exe', 'add', key, '/v', 'no_create_flags', '/t', 'REG_DWORD', '/d', '0x800', '/f')
try:
    text = run('video-flags', fixtures/'video-flags.exe')
    require('video_device_hr=80004005 device_null=1 context_null=1' in text and
            'ordinary_device_hr=00000000 device_valid=1 context_valid=1' in text, 'video-only device fallback')
finally:
    run('restore-video-flags', 'reg.exe', 'delete', key, '/v', 'no_create_flags', '/f')
windows_video = run('video-path', 'winepath.exe', '-w', video).strip()
text = run('video-frames', fixtures/'video-frames.exe', windows_video)
sums = re.findall(r'pixel_sum=(\d+)', text)
require('gpu_content_frames=3' in text and text.count('alpha_zero=0') == 3 and
        len(sums) == 3 and len(set(sums)) > 1, 'changing nonblack opaque GPU video frames')
