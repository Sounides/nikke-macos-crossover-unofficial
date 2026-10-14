# Display and performance verification

Test machine: MacBook Pro M3 Pro, 18 GB RAM, macOS 27.0.1. Built-in display: 3024 × 1964 physical pixels; 1512 × 982 point desktop; ProMotion. PC client 152.8.13, October 13–14, 2026.

## Names and icons

The native Wine bundles have internal folder names `NIKKE.app` and `NIKKE Launcher.app`. During these measurements they also displayed NIKKE and NIKKE Launcher. Both used the same ICNS file as the Applications starter. The native driver retains this icon instead of replacing it with the Windows executable icon. Those restarted app names and menu identity were verified through Computer Use, and signatures and icon equality were checked. A direct Dock-tooltip capture was unavailable. The later public package labels these hosts Unofficial NIKKE Game Host and Unofficial Launcher for NIKKE; this metadata change does not alter the measured rendering path.

## Resolution

The initial game rendered a 1388 × 781 buffer enlarged to 2776 × 1562 physical pixels. The isolated prefix now enables `RetinaMode=Y`; selecting FullScreen through the game's Graphics settings produces a **3024 × 1964 backbuffer and Metal drawable**. Drawable bounds are 1512 × 982 points at scale 2. A known test image with alternating black/white stripes shows one stripe per physical pixel. MetalFX upscaling is not enabled.

Choose **FullScreen**, **60 FPS** and **Save** in the game. macOS's green window button alone does not establish the game's buffer resolution. Do not set Wine's `LogPixels` to 192: that experiment caused input-coordinate problems; the original absent value was restored.

## Color

The actual presentation layer reports BGRA8Unorm (Metal format 80), sRGB, SDR/EDR off. The display's Color LCD ICC profile is present. A known sRGB color fixture was captured through Computer Use and converted from its embedded ICC profile to sRGB: gray levels 0/16/64/128/192/235/255 were exact; primary-color errors were at most three 8-bit levels in the JPEG capture. The native pixel pattern remained sharp.

This verifies the software color route and pixel mapping. It does **not** measure the physical panel's Delta E, white point, luminance or uniformity. That requires a colorimeter and a physical reference measurement. No screenshot-based calibration or arbitrary gamma correction was applied.

True Tone was temporarily off and the display temporarily set to 60 Hz for reference checks. Original **True Tone on, ProMotion, Night Shift off, Apple XDR Display (P3-1600 nits)** were restored and verified through System Settings. Brightness and automatic brightness were preserved. True Tone intentionally adapts the visible white point to ambient light.

## Actual combat measurements

FPS uses the Metal drawable's positive, actual `presentedTime`, not CPU submission frequency or a menu counter. A phase is accepted as combat only when captured images at both endpoints show the active battle HUD. Half-second margins exclude endpoint captures. Loading, story, boss introductions and result screens are excluded. The private shader cache is retained between runs.

| Route and normal game settings | Combat | Duration | Delivered FPS | 99th percentile interval | Worst interval |
| --- | --- | ---: | ---: | ---: | ---: |
| WineD3D/Vulkan, 2× AA, Max effects, Bloom on | 2-5 | 8.98 s | 44.75 | 33.33 ms | 50.00 ms |
| WineD3D/Vulkan, 2× AA, Balanced effects, Bloom off | 2-6 | 8.98 s | 50.76 | 25.00 ms | 33.33 ms |
| DXMT, 2× AA, Balanced effects, Bloom off | 2-9 | 22.69 s | 59.71 | 16.67 ms | 33.33 ms |
| DXMT, 2× AA, Balanced effects, Bloom off | 2-10 | 19.07 s | 58.45 | 25.00 ms | 258.33 ms |
| DXMT, AA off, effects off, High characters, Bloom off | 2-11 | 19.08 s | 56.49 | 25.00 ms | 66.67 ms |

These are different encounters, not controlled comparisons of identical scenes. DXMT substantially improves performance, but **constant 60 fps is not achieved by these measurements**. The best sample still has eleven intervals above 20 ms. Lowering effects did not eliminate missed frames in the later tested encounter.

The scheduling experiment averaged 58.83 fps over 19.72 seconds of Simulation 1-A combat, with 35 intervals above 20 ms and a 75 ms worst interval. It does not establish an improvement. Native Metal performance telemetry for the same combat phase reports about 5.48 ms average on-GPU wall time (29.63 ms maximum) and 2.58 ms average in-flight CPU wall time (34.68 ms maximum). These include pipeline timing and synchronization; they are not a CPU instruction profiler. The Metal HUD explicitly reports Game Mode off in the borderless game view.

In the 2-10 sample, long intervals coincided with delays before the next Metal drawable request; drawable acquisition itself was short. This points beyond acquisition waiting alone, but does not distinguish game CPU work, shader compilation, renderer synchronization, GPU fences or scheduling. A CPU profile of the lobby is not combat bottleneck proof. The UI-thread QoS and Game Mode eligibility metadata are opt-in experiments and are not represented as a validated fix. Extending QoS to all Windows worker threads still measured 58.79 fps in Simulation 1-A stage 2 (14.08 seconds, 41.67 ms worst interval); that extension was reverted. Native window/fullscreen resizing was verified, then the exact 3024 × 1964 game mode restored.

A 120 Hz Metal limit while keeping the game at 60 averaged 59.58 fps in Simulation 1-A stage 3, with 66 intervals above 20 ms over 14.10 seconds and a 50 ms worst interval. It was less even than the 60 limit and was not selected as the default. The runner permits an explicitly supplied DXMT_CONFIG for diagnostics; its normal configuration remains 60.

Rejected experiments: an additional CPU producer cap, deadline drawable wrappers and asynchronous MoltenVK submission. They either worsened pacing, reduced performance or introduced startup problems. They are not enabled in the shipped runner; the producer/deadline wrappers are removed from the source.

The shipped DXMT runner requests Metal pacing at 60 and uses a private shader cache. It preserves native resolution and the original game/ACE files. Sustained 60 across encounters and long sessions remains an open performance objective.

## Reproduce a timing check

Use a new metrics path for each test; the observer opens its CSV once per game process. The updated observer exclusively creates files and uses a unique suffix if the requested path already exists, preserving previous recordings. Then:

```bash
NIKKE_METAL_METRICS_FILE="$NIKKE_WORK/logs/presentation.csv" \
  bash scripts/run.sh "$NIKKE_WORK" launch
```

Use the official Launch button. Record the active combat phase and exclude transitions, captures and unrelated workloads. Run `python3 scripts/analyze-presentation.py CSV --start MONOTONIC_SECONDS --end MONOTONIC_SECONDS` for a selected phase. A last-60-second sample without visual phase verification must not be described as combat. Simulation encounters can vary after a reset, even within the same numbered stage; do not describe those as identical enemy workloads. Do not publish account-bearing captures or logs.


The source for the known-color image is `tests/display-colors.c`. It draws 1024 × 512 physical pixels with gray levels, primaries and one-pixel stripes. Compile it with the prepared x64 MinGW compiler, linking `-ld3d11 -ldxgi -ld3dcompiler -luuid`. Run it only in an idle isolated prefix. For the DXMT fixture, select `NIKKE_DXMT=1`, `NIKKE_DXMT_TARGET=display-colors.exe` and native DXGI/Winemetal overrides for that owned executable. The fixture is not an in-game performance benchmark or a physical-panel calibration tool.


A final physical-display 60 Hz comparison with the normal Metal 60 limit, Basic character textures, AA/effects/Bloom off and native 3024 × 1964 output measured 56.88 fps in Simulation 1-A stage 5 (14.10 seconds, p99 33.33 ms, worst 250 ms). Both endpoint images show active combat. This is a different boss workload, so it does not isolate the display change's effect, but it confirms that fixed 60 Hz is not sufficient to achieve the objective. ProMotion was restored and verified again after this test. No global refresh change is automated by the app.

The unresolved blocker is missed presentation deadlines during actual combat, including occasional long production/synchronization intervals. Average GPU headroom alone is insufficient to establish a fix; the precise producer/synchronization/compilation cause remains unisolated. The source package is usable and reproducible, while the sustained constant-60 objective remains open.


The normal shipped path uses an ordinary `CAMetalLayer`; the custom presentation observer runs only when its environment variable is explicitly set. Native macOS telemetry without that observer independently confirms the 3024 × 1964 BGRA8Unorm layer. A further visually bounded combat sample on this path is pending; loading/menu telemetry is not substituted for combat evidence. One startup after the live-refresh test reported a GC suspension-loop failure, then recovered on a normal official-launcher retry. See TROUBLESHOOTING.md.
