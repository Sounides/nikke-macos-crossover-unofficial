#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
set -euo pipefail
umask 077
[[ $# -eq 1 ]] || { echo 'Usage: setup-prefix.sh WORK_ROOT' >&2; exit 2; }
task_work="$(cd "$1" && pwd)"
export WINEPREFIX="$task_work/custom-prefix"
export WINEDEBUG='-all,err+all'
export WINEDLLOVERRIDES='mscoree,mshtml='
wine_runtime="$task_work/runtime/bin/wine"
mkdir -p "$task_work/logs"
[[ -x "$wine_runtime" ]] || { echo 'Build the runtime first.' >&2; exit 1; }
case "${NIKKE_LAUNCHER_STANDARD_DPI:-1}" in 0|1) ;; *) echo 'NIKKE_LAUNCHER_STANDARD_DPI must be 0 or 1.' >&2; exit 2;; esac
"$wine_runtime" wineboot.exe -u >> "$task_work/logs/prefix-setup.log" 2>&1
"$wine_runtime" reg.exe add 'HKCU\Software\Wine\Direct3D' /v renderer /t REG_SZ /d vulkan /f \
  >> "$task_work/logs/prefix-setup.log" 2>&1
"$wine_runtime" reg.exe add 'HKCU\Software\Wine\AppDefaults\nikke.exe\Direct3D' \
  /v no_create_flags /t REG_DWORD /d 0x800 /f >> "$task_work/logs/prefix-setup.log" 2>&1
"$wine_runtime" reg.exe add 'HKCU\Software\Wine\Mac Driver' /v RetinaMode /t REG_SZ /d Y /f \
  >> "$task_work/logs/prefix-setup.log" 2>&1
# Keep one shared native monitor coordinate system. DPI-unaware virtualization
# scales the launcher's lower-resolution rendering; the game's PerMonitorV2
# manifest continues to request physical pixels. This affects only this prefix.
task_dpi_root='HKLM\Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options'
if [[ "${NIKKE_LAUNCHER_STANDARD_DPI:-1}" == 1 ]]; then
  "$wine_runtime" reg.exe add 'HKCU\Control Panel\Desktop' /v LogPixels /t REG_DWORD /d 192 /f \
    >> "$task_work/logs/prefix-setup.log" 2>&1
  for task_image in nikke_launcher.exe intl_service.exe tbs_browser.exe INTLWebViewHelper.exe; do
    task_dpi_key="$task_dpi_root\\$task_image"
    "$wine_runtime" reg.exe add \
      "$task_dpi_key" \
      /v dpiAwareness /t REG_DWORD /d 0 /f >> "$task_work/logs/prefix-setup.log" 2>&1
  done
else
  "$wine_runtime" reg.exe add 'HKCU\Control Panel\Desktop' /v LogPixels /t REG_DWORD /d 96 /f \
    >> "$task_work/logs/prefix-setup.log" 2>&1
  for task_image in nikke_launcher.exe intl_service.exe tbs_browser.exe INTLWebViewHelper.exe; do
    task_dpi_key="$task_dpi_root\\$task_image"
    "$wine_runtime" reg.exe delete \
      "$task_dpi_key" \
      /v dpiAwareness /f >> "$task_work/logs/prefix-setup.log" 2>&1 || true
  done
fi
media_root="$task_work/runtime/Frameworks/GStreamer.framework/Versions/1.0"
export GST_PLUGIN_SYSTEM_PATH_1_0="$media_root/lib/gstreamer-nikke"
export GST_PLUGIN_PATH_1_0=''
export GST_REGISTRY_1_0="$task_work/gst-registry-nikke-x86_64.bin"
export GST_REGISTRY_FORK=no
export GIO_MODULE_DIR="$media_root/lib/gio/modules"
"$wine_runtime" 'C:\windows\system32\regsvr32.exe' /s winegstreamer.dll >> "$task_work/logs/prefix-setup.log" 2>&1
"$wine_runtime" 'C:\windows\syswow64\regsvr32.exe' /s winegstreamer.dll >> "$task_work/logs/prefix-setup.log" 2>&1
# Retire the prefix's cached monitor DPI before the next application starts.
WINEPREFIX="$WINEPREFIX" "$task_work/runtime/bin/wineserver" -k \
  >> "$task_work/logs/prefix-setup.log" 2>&1 || true
WINEPREFIX="$WINEPREFIX" "$task_work/runtime/bin/wineserver" -w \
  >> "$task_work/logs/prefix-setup.log" 2>&1
echo 'Isolated prefix prepared. Download the official miniloader and run scripts/run.sh WORK_ROOT install /absolute/path/to/installer.exe'
