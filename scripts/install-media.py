#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Install selected media modules into the newly built runtime, before prefix setup."""
from pathlib import Path
import shutil
import sys
root = Path(sys.argv[1]).resolve()
for arch in ('x86_64-windows', 'i386-windows'):
    for module in ('winegstreamer', 'mfplat', 'mfreadwrite', 'mf', 'd3d11', 'dxgi', 'wined3d'):
        source = root/'build-media/dlls'/module/arch/(module+'.dll')
        target = root/'runtime/lib/wine'/arch/(module+'.dll')
        shutil.copy2(source, target)
shutil.copy2(root/'build-media/dlls/winegstreamer/winegstreamer.so', root/'runtime/lib/wine/x86_64-unix/winegstreamer.so')
print('Selected media modules installed')
