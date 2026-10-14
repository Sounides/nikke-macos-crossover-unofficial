#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Verify the published patch against the exact pinned Wine source archive."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

repo = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive', type=Path)
args = parser.parse_args()
expected_input = next(i for i in json.loads((repo/'inputs.json').read_text()) if i['file']=='wine-11.18.tar.gz')
digest = hashlib.sha256(args.archive.read_bytes()).hexdigest()
if digest != expected_input['sha256']:
    raise SystemExit('Wine archive checksum mismatch')
expected = json.loads((repo/'patches/source-checksums.json').read_text())
with tempfile.TemporaryDirectory(prefix='nikke-patch-check-') as temporary:
    root = Path(temporary)
    with tarfile.open(args.archive) as archive:
        for name in expected:
            try:
                source = archive.extractfile('wine-wine-11.18/'+name)
            except KeyError:
                # The combined patch also creates the new DXMT bridge source.
                continue
            if source is None: raise RuntimeError('Missing source: '+name)
            dest = root/name; dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(source.read())
    subprocess.run(['patch', '--fuzz=0', '-p1', '-i', str(repo/'patches/nikke-wine-11.18.patch')], cwd=root, check=True)
    for name, wanted in expected.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != wanted:
            raise RuntimeError('Patched source mismatch: '+name)
print('PASS: zero-fuzz patch and exact source hashes for', len(expected), 'files')
