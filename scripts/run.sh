#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
set -euo pipefail
umask 077
if [[ $# -lt 1 ]]; then
  echo 'Usage: run.sh WORK_ROOT [launch | install INSTALLER.exe | stop]' >&2
  exit 2
fi
task_work="$(cd "$1" && pwd)"
shift
export WINEPREFIX="$task_work/custom-prefix"
export NIKKE_WINE_APP_LOADER="$task_work/runtime/lib/wine/x86_64-unix/NIKKE Launcher.app/Contents/MacOS/wine"
export NIKKE_WINE_APP_TARGET='nikke_launcher.exe'
export NIKKE_WINE_HELPER_LOADER="$task_work/runtime/lib/wine/x86_64-unix/Wine Helpers.app/Contents/MacOS/wine"
export NIKKE_WINE_GAME_APP_LOADER="$task_work/runtime/lib/wine/x86_64-unix/NIKKE.app/Contents/MacOS/wine"
export WINEDLLOVERRIDES='mscoree,mshtml='
export WINEDEBUG='-all,err+all'
export NIKKE_CEF_SOFTWARE="${NIKKE_CEF_SOFTWARE:-0}"
if [[ -f "$task_work/dxmt-enabled" ]]; then
  export NIKKE_DXMT=1
  export DXMT_CONFIG="${DXMT_CONFIG:-d3d11.preferredMaxFrameRate=60}"
  export NIKKE_DISPLAY_FPS="${NIKKE_DISPLAY_FPS:-60}"
  export DXMT_SHADER_CACHE_PATH="$task_work/dxmt-shader-cache"
  mkdir -p "$DXMT_SHADER_CACHE_PATH"
fi
media_root="$task_work/runtime/Frameworks/GStreamer.framework/Versions/1.0"
export GST_PLUGIN_SYSTEM_PATH_1_0="$media_root/lib/gstreamer-nikke"
export GST_PLUGIN_PATH_1_0=''
export GST_REGISTRY_1_0="$task_work/gst-registry-nikke-x86_64.bin"
export GST_REGISTRY_FORK=no
export GIO_MODULE_DIR="$media_root/lib/gio/modules"
wine_runtime="$task_work/runtime/bin/wine"
mkdir -p "$task_work/logs"
[[ -x "$wine_runtime" ]] || { echo 'Build the isolated Wine runtime first.' >&2; exit 1; }
case "${1:-launch}" in
  launch)
    [[ -f "$WINEPREFIX/drive_c/NIKKE/Launcher/nikke_launcher.exe" ]] || {
      echo 'Install the official NIKKE launcher into C:\NIKKE first.' >&2; exit 1;
    }
    "$wine_runtime" reg.exe add 'HKCU\Software\Wine\AppDefaults\nikke.exe\Direct3D' \
      /v no_create_flags /t REG_DWORD /d 0x800 /f \
      >> "$task_work/logs/video-setting.log" 2>&1
    exec "$wine_runtime" 'C:\NIKKE\Launcher\nikke_launcher.exe' \
      >> "$task_work/logs/launcher.log" 2>&1
    ;;
  install)
    [[ $# -eq 2 && -f "$2" ]] || { echo 'Provide the official miniloader EXE.' >&2; exit 2; }
    exec "$wine_runtime" "$2" /S /Silent >> "$task_work/logs/installer.log" 2>&1
    ;;
  stop)
    "$wine_runtime" taskkill.exe /im nikke.exe /t /f >> "$task_work/logs/stop.log" 2>&1 || true
    "$wine_runtime" taskkill.exe /im nikke_launcher.exe /t /f >> "$task_work/logs/stop.log" 2>&1 || true
    ;;
  *) echo 'Usage: run.sh WORK_ROOT [launch | install INSTALLER.exe | stop]' >&2; exit 2 ;;
esac
