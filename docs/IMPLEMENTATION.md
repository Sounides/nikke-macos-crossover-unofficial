# Compatibility changes

Apply `patches/nikke-wine-11.18.patch` exactly once to pristine Wine 11.18 with `patch --fuzz=0 -p1`. Generated server protocol files are included. The DLLs and wineserver must be built together; the patch changes the server protocol to 963.

## Launcher and download

The launcher renders through a browser process whose child window belongs to another process. Wine's Mac driver now hosts the remote Metal surface in its owning root window, positions and clips each child, maintains paint order, retires replaced surfaces and updates moved/resized children. Retina coordinate conversion occurs at the native boundary. Input translation retains the child's actual window origin.

The white outline fix transforms a remote surface to cover at most a one-Win32-pixel gap at the outer edge. Enlarging the host's frame alone left the CAContext content at its original size. Interior siblings, hidden/zero-size surfaces and gaps larger than one pixel retain their geometry. No launcher CSS or executable bytes are changed.

A downloader-specific one-second startup delay allows VersionService's IPC pipe to become ready. A valid multibyte NOP implementation avoids a Rosetta instruction failure.

Native Wine loader routing separates launcher, background helpers and the game into local app bundles. `NIKKE_WINE_GAME_APP_LOADER` selects the game UI process using its real spawn image. The generated hosts display **Unofficial Launcher for NIKKE** and **Unofficial NIKKE Game Host**. Internal folders remain `NIKKE Launcher.app` and `NIKKE.app` and their routing identifiers remain stable; the game runs its original protected entry point. No official Windows executable is renamed.

The `WineUseBundleIcon` Info.plist option keeps the native bundled icon instead of adopting a Windows executable icon. It is enabled only for the two visible NIKKE bundles.

Owned shadow/tool windows are suppressed at native ordering while an owner
is minimized. State changes also synchronize same-process owned windows.
Tracking distinguishes suppressed windows from otherwise hidden popups, so
restoring the owner respects current Win32 visibility and layered readiness.
This addresses the four surviving shadow windows around the launcher's icon
rectangle. See [launcher display behavior](LAUNCHER-DISPLAY.md).

## Protected startup and Wine kernel behavior

The retained changes implement or correct Wine APIs used by the installed drivers: driver return-address tagging and untagging, service-name formatting, process exit status, locked-MDL mapping lifetime, driver-module enumeration, real virtual-memory copying, process-local object CREATE callbacks with access filtering, virtual System-process identity, asynchronous System work items and real UserMode thread-context retrieval.

On macOS/x86_64, Wine's SIGSYS handler selected native pthread thread-local storage and resumed the Windows syscall dispatcher without restoring the Windows TEB in GS. Ordinary DLL calls could work while raw Windows syscalls failed. Calling `leave_handler` before resuming fixes that context transition. The original protected game bootstrap then proceeds into Unity, authentication and gameplay.

There is no bootstrap skip in the final patch. `kernel32/thread.c` is unchanged from pristine Wine 11.18. Game and ACE files were preserved. Wine's emulated kernel still has limits: global user-mode/duplicate-handle notifications, physical `MmCopyMemory` and KernelMode context retrieval remain incomplete. Passing the tested startup path does not establish full Windows/ACE feature parity.

## Movies and graphics

The base graphics route is Vulkan-backed WineD3D through MoltenVK. The faster tested game route uses the optional private DXMT installation described below. Typed-UAV format support is derived from backend capabilities. Ordinary unshared DXGI resources return `S_OK` and a null shared handle; actual shared resources and invalid NT-handle queries preserve their failures.

[Wine MR 11398](https://gitlab.winehq.org/wine/wine/-/merge_requests/11398), by Stian Low, supplies `no_create_flags`. The runner sets:

```text
HKCU\Software\Wine\AppDefaults\nikke.exe\Direct3D
no_create_flags = REG_DWORD 0x800
```

This rejects requested `D3D11_CREATE_DEVICE_VIDEO_SUPPORT`, allowing Unity to select its software decoder. Ordinary D3D11 graphics continue to work. GStreamer 1.28.8 and Wine's Media Foundation modules supply the codecs. The title's actual changing movie frames were verified. Cross-device shared video textures remain unsupported.

Undo the video setting with the isolated runtime:

```bash
WINEPREFIX="$NIKKE_WORK/custom-prefix" "$NIKKE_WORK/runtime/bin/wine" reg.exe delete \
  'HKCU\Software\Wine\AppDefaults\nikke.exe\Direct3D' /v no_create_flags /f
```

The runner reapplies the setting on launch, so remove its registry command as well if deliberately testing the original path.

## Runtime assembly

The main build installs the loader, server, native Mac driver and ntdll, and standard PE DLLs. A separate GStreamer-enabled build supplies native `winegstreamer.so` and both architectures of `winegstreamer`, `mfplat`, `mfreadwrite`, `mf`, `d3d11`, `dxgi` and `wined3d`. Prefix setup then initializes the fresh prefix and registers both architectures of `winegstreamer`.

The repository's preparation script copies four private dependency libraries, rewrites their local dependency references and signs those copies. Framework dependencies are relocated relative to their loader. Wine's own configured library paths still refer to the chosen work root. Rebuild rather than move that root. No installed CrossOver files, global codecs or Mac security settings are changed.


## Optional DXMT bridge and Retina presentation

The new `dlls/winemac.drv/dxmt.c` exports the legacy `macdrv_functions` interface used by the tested DXMT donor. It translates the interface into Wine 11.18 client surfaces, registers them with the existing window lifecycle, and releases the Metal view and client surface together. This is a compatibility bridge in Wine; the DXMT project is not modified.

The 64-bit Wine D3D11 entry point uses the private `nikke_dxmt.dll` only when `NIKKE_DXMT=1` and the actual executable basename is `nikke.exe`. Unsupported VIDEO_SUPPORT requests return failure with null outputs, preserving the tested software movie decoder. Ordinary graphics creation forwards all parameters unchanged. `NIKKE_DXMT_TARGET` exists for owned test fixtures. It is not set by the game runner.

The installation script copies the donor's D3D11/DXGI/Winemetal modules, clears the Wine built-in redirection marker in the two private PE copies, and sets game-specific native DLL overrides. Global overrides retain Wine's built-in D3D11/DXGI so the launcher does not inherit the game backend. Original NIKKE and ACE files are untouched. No copied donor modules are redistributed.

Close this setup before rollback, then use the exact checkpoint printed by installation:

```bash
python3 scripts/install-dxmt.py --work-root "$NIKKE_WORK" \
  --restore "$NIKKE_WORK/checkpoints/dxmt-TIMESTAMP"
```

Rollback restores the saved files, marker, and DLL override values. It retains the checkpoint and shader cache. Restoring checkpoints from multiple installations must be done in reverse order.

`RetinaMode=Y` is scoped to the isolated prefix. Native full-screen gameplay uses a 3024 × 1964 backbuffer and drawable on the tested display, with 1512 × 982 point bounds and scale 2. The output is SDR sRGB/BGRA8; native pixel stripes confirm no 2× enlargement of a half-resolution buffer. Other displays require their own measurement.

Prefix setup now uses LogPixels192 and Wine's dpiAwareness0 image option for
the launcher and its three browser helpers. Their standard-DPI rendering is
pixel-doubled while monitor coordinates stay consistent. The game's original
PerMonitorV2 manifest is retained; an owned DXMT fixture confirms native
3024 × 1964 output in this profile. No application-specific RetinaMode override
is used. The prior 96-DPI profile is available through prefix setup's documented
NIKKE_LAUNCHER_STANDARD_DPI=0 option.

The optional `NIKKE_METAL_METRICS_FILE` observer writes only actual Metal presentation timestamps and surface metadata to a local CSV. Logging runs on a separate serial queue. Zero presentation timestamps are excluded from FPS counts. `NIKKE_DISPLAY_FPS=60` requests a game-only CADisplayLink cadence; `DXMT_CONFIG=d3d11.preferredMaxFrameRate=60` requests DXMT's Metal pacing. Neither changes global display preferences. Rejected CPU/deadline pacer experiments are absent from this patch.

`NIKKE_GAME_QOS=1` is an optional scheduling experiment for the game bundle's Mac UI threads. It is not a default or a demonstrated constant-60 fix. Game Mode eligibility metadata is supplied; actual Game Mode activation is not claimed. `NIKKE_VSYNC=1` is an optional WineD3D FIFO presentation experiment, unused by the default DXMT runner.


## October 14 review integration

MDL tracking now records each section view's AllocationBase, so an unmap
address outside the locked byte subranges still defers release. Deferred
unmapping moves to another MDL referencing the same allocation and executes
only after its last reference is removed. Failure to allocate tracking state
fails mapping instead of returning an unprotected view. Unlocking clears a
cached mapping, and unsupported fixed-address requests fail explicitly.
See NOTICE.md for the LGPL reference and tests/mdl-mapping.c for the
nonoverlapping-range regression.

The optional NIKKE_CEF_SOFTWARE=1 path appends only missing software-rendering
switches to intl_service.exe. Other executable names and the default path
retain their command lines. No official service wrapper is installed, so
updater-conflict handling for such a wrapper is inapplicable. Installer and
DXMT rollback behavior otherwise remains as documented and previously tested.
No failed experimental kernel callback implementation is imported.
