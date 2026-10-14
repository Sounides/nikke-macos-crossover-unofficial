#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Prepare pinned source, toolchain, codecs and private dependency copies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

repo = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work-root', required=True, type=Path)
parser.add_argument('--cache', required=True, type=Path)
parser.add_argument('--dependency-libs', required=True, type=Path, help='CrossOver lib/x86_64 directory; read only')
parser.add_argument('--fetch', action='store_true', help='Download missing pinned inputs')
args = parser.parse_args()
root, cache = args.work_root.resolve(), args.cache.resolve()
if root.is_relative_to(repo):
    parser.error('Keep the work root outside the source repository')
if any(c.isspace() for c in str(root)):
    parser.error('Use a work root without whitespace; Wine compiler flags embed this path')
root.mkdir(parents=True, exist_ok=True); cache.mkdir(parents=True, exist_ok=True)
if (root/'wine-source').exists():
    parser.error('wine-source already exists; use a fresh work root to avoid applying the patch twice')
inputs = json.loads((repo/'inputs.json').read_text())

def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''): result.update(chunk)
    return result.hexdigest()

def safe_extract(archive_path, target, select=lambda member: True):
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path) as archive:
        selected = [m for m in archive.getmembers() if select(m)]
        for member in selected:
            name = Path(member.name)
            if name.is_absolute() or '..' in name.parts:
                raise RuntimeError('Unsafe archive member')
            if member.issym() or member.islnk():
                base = name.parent if member.issym() else Path('.')
                resolved = (target/base/member.linkname).resolve()
                if not resolved.is_relative_to(target.resolve()):
                    raise RuntimeError('Unsafe archive link')
            elif not (member.isfile() or member.isdir()):
                raise RuntimeError('Unsupported archive member')
        archive.extractall(target, members=selected)

for item in inputs:
    path = cache/item['file']
    if not path.exists():
        if not args.fetch: parser.error('Missing cached input: '+item['file']+'; add --fetch to download it')
        partial = path.with_suffix(path.suffix+'.part')
        subprocess.run(['curl', '--fail', '--location', '--retry', '3', item['url'], '-o', str(partial)], check=True)
        if sha256(partial) != item['sha256']: raise RuntimeError('Checksum mismatch: '+item['file'])
        partial.rename(path)
    if sha256(path) != item['sha256']: raise RuntimeError('Checksum mismatch: '+item['file'])
print('All six pinned input checksums passed', flush=True)

safe_extract(cache/'wine-11.18.tar.gz', root/'source-extract')
(root/'source-extract/wine-wine-11.18').rename(root/'wine-source')
subprocess.run(['patch', '--fuzz=0', '-p1', '-i', str(repo/'patches/nikke-wine-11.18.patch')], cwd=root/'wine-source', check=True)
expected = json.loads((repo/'patches/source-checksums.json').read_text())
for name, digest in expected.items():
    if sha256(root/'wine-source'/name) != digest: raise RuntimeError('Patched source mismatch: '+name)
safe_extract(cache/'llvm-mingw.tar.xz', root/'toolchain')
safe_extract(cache/'bison.tar.xz', root/'toolchain')
safe_extract(cache/'crossover-sources-26.3.0.tar.gz', root/'headers-extract',
             lambda m: m.name.startswith(('sources/freetype/include/', 'sources/gnutls/gnutls/lib/includes/')))
headers = root/'headers-extract/sources'
deps = root/'deps'; deps.mkdir(exist_ok=True)
shutil.copytree(headers/'freetype/include', deps/'freetype', symlinks=True)
shutil.copytree(headers/'gnutls/gnutls/lib/includes', deps/'gnutls', symlinks=True)
template = deps/'gnutls/gnutls/gnutls.h.in'
text = template.read_text()
for key,value in {'VERSION':'3.8.3','MAJOR_VERSION':'3','MINOR_VERSION':'8','PATCH_VERSION':'3',
                  'NUMBER_VERSION':'0x030803','DEFINE_IOVEC_T':'typedef struct iovec giovec_t;'}.items():
    text = text.replace('@'+key+'@', value)
template.with_name('gnutls.h').write_text(text)
libs = deps/'lib'; libs.mkdir()
for name in ('libfreetype.6.dylib', 'libgnutls.30.dylib', 'libgmp.10.dylib', 'libMoltenVK.dylib'):
    source = args.dependency_libs/name
    if not source.is_file(): parser.error('Missing dependency library: '+name)
    shutil.copy2(source.resolve(), libs/name)
for name,target in [('libfreetype.dylib','libfreetype.6.dylib'),('libgnutls.dylib','libgnutls.30.dylib')]:
    (libs/name).symlink_to(target)
for binary in libs.glob('*.dylib'):
    if binary.is_symlink(): continue
    deps_output = subprocess.check_output(['otool', '-L', str(binary)], text=True)
    changes = []
    for line in deps_output.splitlines()[1:]:
        dependency = line.strip().split(' (compatibility version')[0]
        basename = Path(dependency).name
        if basename in ('libfreetype.6.dylib','libgnutls.30.dylib','libgmp.10.dylib','libMoltenVK.dylib'):
            changes += ['-change', dependency, '@loader_path/'+basename]
        elif dependency.startswith(('/opt/', '/Applications/', '/Users/')):
            raise RuntimeError('Unexpected external dependency: '+dependency)
    subprocess.run(['install_name_tool', '-id', '@rpath/'+binary.name, *changes, str(binary)], check=True)
    subprocess.run(['codesign', '--force', '--sign', '-', str(binary)], check=True)
for name,label in [('gstreamer-1.0-1.28.8-universal.pkg','media-runtime-pkg'),
                   ('gstreamer-1.0-devel-1.28.8-universal.pkg','media-devel-pkg')]:
    subprocess.run(['pkgutil', '--expand-full', str(cache/name), str(root/label)], check=True)
subprocess.run(['python3', str(repo/'scripts/prepare-gstreamer.py'), '--work-root', str(root),
                str(root/'media-runtime-pkg'), str(root/'media-devel-pkg')], check=True)
print('Prepared source, codecs and private dependency copies at', root)
