#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Check the source publication boundary and recorded file hashes locally.

This catches common publication mistakes. It is not a guarantee that a
secret, license issue, policy violation or account risk cannot exist.
"""
import hashlib
from pathlib import Path
import re

repo = Path(__file__).resolve().parents[1]
records = {}
for line in (repo/'SHA256SUMS').read_text().splitlines():
    digest, name = line.split('  ', 1)
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or name in records or not re.fullmatch('[0-9a-f]{64}', digest):
        raise SystemExit('Invalid source checksum manifest')
    records[name] = digest

allowed_extensions = {'.md', '.txt', '.json', '.patch', '.py', '.sh', '.swift', '.c', '.h', '.yml', '.yaml'}
patterns = [
    rb'/' + rb'Users/[^/\s]+/',
    rb'gh[pousr]_[A-Za-z0-9]{30,}',
    rb'github_pat_[A-Za-z0-9_]{30,}',
    rb'AKIA[0-9A-Z]{16}',
    rb'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----',
    rb'(?i)authorization:\s*bearer\s+[A-Za-z0-9._=-]{20,}',
    rb'https?://[^/\s:]+:[^/\s@]+@',
    rb'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}',
]
actual = set()
for path in repo.rglob('*'):
    name = path.relative_to(repo).as_posix()
    if '.git' in path.relative_to(repo).parts or '__pycache__' in path.relative_to(repo).parts:
        continue
    if path.is_symlink():
        raise SystemExit('Symlinks must not be published: '+name)
    if not path.is_file():
        continue
    if path.name in ('.DS_Store',):
        raise SystemExit('Remove local metadata before publication: '+name)
    if path.suffix not in allowed_extensions and path.name not in ('LICENSE', '.gitignore', 'SHA256SUMS'):
        raise SystemExit('Unexpected publication file type: '+name)
    data = path.read_bytes()
    try:
        data.decode('utf-8')
    except UnicodeDecodeError:
        raise SystemExit('Binary/non-UTF-8 file must not be published: '+name)
    if any(re.search(pattern, data) for pattern in patterns):
        raise SystemExit('Potential private information; review locally: '+name)
    if name != 'SHA256SUMS':
        actual.add(name)
        if hashlib.sha256(data).hexdigest() != records.get(name):
            raise SystemExit('Source checksum mismatch: '+name)
if actual != set(records):
    raise SystemExit('Publication files differ from the checksum manifest')
print('PASS:', len(actual), 'manifested source files; no binaries, symlinks, local user paths or matched secret patterns.')
