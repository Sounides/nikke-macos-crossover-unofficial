#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
set -euo pipefail
[[ $# -eq 1 ]] || { echo 'Usage: build.sh WORK_ROOT' >&2; exit 2; }
task_work="$(cd "$1" && pwd)"
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
jobs="${NIKKE_BUILD_JOBS:-8}"
case "$jobs" in ''|*[!0-9]*) echo 'NIKKE_BUILD_JOBS must be a positive integer.' >&2; exit 2;; esac
[[ "$jobs" -gt 0 ]] || exit 2
mkdir -p "$task_work/logs" "$task_work/build-bison" "$task_work/tools"
toolchain="$task_work/toolchain/llvm-mingw-20261006-ucrt-macos-universal/bin"
export PATH="$task_work/tools/bin:$toolchain:/usr/bin:/bin:/usr/sbin:/sbin"
if [[ ! -x "$task_work/tools/bin/bison" ]]; then
  (
    cd "$task_work/build-bison"
    "$task_work/toolchain/bison-3.8.2/configure" --prefix="$task_work/tools"
    make -j"$jobs"
    make install
  ) > "$task_work/logs/bison-build.log" 2>&1
fi
sdk_root="$(xcrun --sdk macosx --show-sdk-path)"
export CC="$(xcrun --find clang) -arch x86_64"
export CXX="$(xcrun --find clang++) -arch x86_64"
export OBJC="$CC"
export CFLAGS="-O2 -g -isysroot $sdk_root"
export OBJCFLAGS="$CFLAGS"
export LDFLAGS="-isysroot $sdk_root -Wl,-rpath,$task_work/deps/lib -L$task_work/deps/lib"
export FREETYPE_CFLAGS="-I$task_work/deps/freetype"
export FREETYPE_LIBS="-L$task_work/deps/lib -lfreetype"
export GNUTLS_CFLAGS="-I$task_work/deps/gnutls"
export GNUTLS_LIBS="-L$task_work/deps/lib -lgnutls"
export ac_cv_lib_soname_freetype="$task_work/deps/lib/libfreetype.6.dylib"
export ac_cv_lib_soname_gnutls="$task_work/deps/lib/libgnutls.30.dylib"
export ac_cv_lib_soname_MoltenVK="$task_work/deps/lib/libMoltenVK.dylib"
target="x86_64-apple-darwin$(uname -r)"
common=("--prefix=$task_work/runtime" "--host=$target" "--build=$target"
  --enable-archs=i386,x86_64 --enable-win64 --disable-tests
  --without-x --without-wayland --without-alsa --without-pulse
  --without-dbus --without-udev --without-usb --without-cups --without-sane --without-gphoto)
mkdir -p "$task_work/build" "$task_work/build-media"
echo 'Building Wine; progress is in WORK_ROOT/logs/wine-build.log'
(
  cd "$task_work/build"
  "$task_work/wine-source/configure" "${common[@]}" --without-gstreamer
  make -j"$jobs"
  make install
) > "$task_work/logs/wine-build.log" 2>&1
media_root="$task_work/runtime/Frameworks/GStreamer.framework/Versions/1.0"
export GSTREAMER_CFLAGS="-I$media_root/include/gstreamer-1.0 -I$media_root/include/glib-2.0 -I$media_root/lib/glib-2.0/include"
export GSTREAMER_LIBS="-L$media_root/lib -Wl,-rpath,$media_root/lib -lgstvideo-1.0 -lgstaudio-1.0 -lgsttag-1.0 -lgstbase-1.0 -lgstreamer-1.0 -lgobject-2.0 -lglib-2.0"
export DYLD_LIBRARY_PATH="$media_root/lib"
echo 'Building Media Foundation modules; progress is in WORK_ROOT/logs/media-build.log'
(
  cd "$task_work/build-media"
  "$task_work/wine-source/configure" "${common[@]}" "--with-wine-tools=$task_work/build" --with-gstreamer
  make -j"$jobs" dlls/winegstreamer/all dlls/mfplat/all dlls/mfreadwrite/all dlls/mf/all \
    dlls/d3d11/all dlls/dxgi/all dlls/wined3d/all
) > "$task_work/logs/media-build.log" 2>&1
python3 "$repo_root/scripts/install-media.py" "$task_work"
python3 "$repo_root/scripts/prepare-wine-apps.py" --work-root "$task_work"
echo 'Runtime built. Next run scripts/setup-prefix.sh WORK_ROOT'
