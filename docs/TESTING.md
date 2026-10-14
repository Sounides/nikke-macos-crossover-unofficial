# Tested behavior and boundaries

Snapshot: October 13–14, 2026. M3 Pro / 18 GB RAM / macOS 27.0.1 / Wine 11.18 under Rosetta / NIKKE.PC_Official_GL_152.8.13 / NA.

| Area | Verified result |
| --- | --- |
| Official miniloader | Fresh download of the launcher completed; no transferred game installation used |
| Launcher | Normal rendering, input, sign-in, download and Launch button |
| White outline | Absent after native remote-layer transform fix and launcher restart |
| Movies | Animated title movie visibly changes; RGB32/ARGB32 fixtures decode three nonblack changing GPU frames |
| Protected startup | Original executable entry and ACE initialization reach normal authentication and saved gameplay |
| Gameplay | Protected gameplay completed through chapter 2 / boss 2-12; rewards and chapter progression appeared |
| Input | User reported normal manual aiming/firing; Computer Use held clicks were unreliable |
| Raw syscalls | Four clean checks: real event signaling, invalid-handle failure, system time, six-argument virtual-memory query |
| Driver compatibility | Object CREATE callback/access filtering, System identity, thread context, process status and typed-UAV readback fixtures passed |
| Retina | Native 3024 × 1964 backbuffer and drawable, scale 2; one-pixel fixture verified |
| Color | sRGB/SDR route and reference pixel values verified; physical panel calibration not measured |
| Performance | DXMT combat samples 56.49–59.71 fps; constant 60 remains open |
| Patch | Zero-fuzz application and byte equality of all 39 changed files against pristine Wine 11.18 |

The entry adapter used during an earlier diagnostic phase was removed from source and both installed kernel32 architectures before final protected-startup verification. No adapter enable option is distributed. Removing it does not erase that test account's earlier history.

ACE-BASE.sys was observed loaded in the isolated Wine driver host, and ACE setup/service helpers exited successfully. Core1/Core2 initialization IOCTLs passed during diagnosis. These observations establish the tested startup behavior; they do not establish persistent operation of every ACE component or full monitoring coverage.

Unverified: account-sanction safety, publisher acceptance, every anti-cheat feature, every movie, later chapters, multiplayer, long sessions, different client/server releases, and other hardware/OS/dependency versions. Do not describe this as an issue-free official Mac port.

Repository-build and Applications-app verification results are recorded in [release checks](RELEASE-CHECKS.txt). Full account-bearing logs and screenshots are intentionally excluded.

See [display/performance details](DISPLAY-PERFORMANCE.md) for actual combat intervals, settings restoration, rejected experiments and measurement limits.


## October 14 review integration

Both architectures of the revised ntoskrnl.exe and kernelbase.dll built and
were installed into the existing isolated DXMT runtime with a rollback
checkpoint. The other 37 patched source files were unchanged. The full
39-file patch again applies with zero fuzz and matches recorded source hashes.
The earlier complete build remains the base; a new full clean build of every
unchanged module was not repeated for this two-module update.

The packaged account-free kernel suite passed allocation-wide nonoverlapping
MDL references, an unmap outside locked subranges, repeated mapping, last
reference release, unsupported fixed-address rejection, register equality for
UserMode thread context, seven CEF subprocess cases, eight x64/x86 valid and
invalid NOP cases, driver/service identity, kernel thread context/return,
System work items and running/exited process status. Each suite run creates
its own prefix under kernel-test-prefix. A stale-service repeatability issue
in the first harness was corrected; the current harness passed afterward.
Allocator exhaustion handling was reviewed in code, not fault-injected.

The installed DXMT route then passed raw syscalls, VIDEO_SUPPORT rejection
with ordinary graphics success, and three changing opaque/nonblack frames
from a newly generated H.264 fixture. No game media was distributed.
The normal Applications starter retains its icon and verifies its signature.
The user confirmed that the updated official Launch reaches the lobby.
Computer Use could not independently capture this window because its app
access was denied. A newly issued real CAPTCHA in this DXMT build remains
unverified; owned subprocess coverage is not substituted for that evidence.

## Public naming and update assessment

The public starter was rebuilt in a private test directory as Unofficial
Launcher for NIKKE; the two Wine hosts display Unofficial Launcher for NIKKE
and Unofficial NIKKE Game Host. Compilation/signatures, matching icons and
label/icon persistence after re-running bundle preparation passed. This
check did not rename or replace the existing working Applications app.

The owned update fixture passed 32-bit launcher/helper file replacement,
parent exit, automatic restart and a replaced 64-bit game launch. Environment,
video/DLL settings and owned preference files survived; sampled runtime files
were unchanged. No account or vendor files were used. This does not test an
actual official version transition, future CEF rendering or new ACE behavior.
See [the update assessment](UPDATES.md).

## Launcher minimize and DPI profile

The actual launcher showed an iconic main window plus four still-visible
layered tool windows around its icon rectangle. An owned fixture reproduced
four native orphan windows with the old module and zero with the revised
module. Restoring the owner showed the root plus only three still-visible
popups; the fourth was explicitly hidden during minimization. The revised
native Mac driver built and was atomically installed with a rollback checkpoint.

The published window regression passed against the installed native driver
in its own account-free prefix. It checks native visibility/geometry, standard
DPI despite a DPI-awareness request, and all three owned browser-helper images.
Initial sampling was too early for asynchronous native geometry; the harness
now waits for the expected frame as well as the expected window count.

The split profile retains RetinaModeY and uses LogPixels192 plus Wine's
dpiAwareness0 option for the launcher and three browser helper images. A real
capture caught the quarter-window failure when only the launcher was configured;
configuring its browser helpers fixed the filled 1348 × 904 point window.
The signed-in state survived the restart. No game or ACE file was modified.
The existing render observer reports the actual browser backbuffer at
1346 × 902 pixels inside that point-sized launcher window; its native physical
capture is 2696 × 1808. This confirms standard-resolution source rendering.

In the same profile, an owned full-screen DXMT fixture produced a
3024 × 1964 backbuffer and capture / 1512 × 982 point window. Its native pixel
stripes alternated every physical pixel; the standard-DPI fixture showed pixel
doubling. Installed DXMT raw-syscall, video-only rejection and three changing
opaque GPU-video checks passed after the native module/profile update.

The user then minimized/restored the actual launcher and used Launch. They
confirmed that the shadow box disappears and that the game renders at Retina
resolution. A native window-list check independently showed the minimized
launcher and all four shadow windows offscreen. The actual game's Metal
drawable measured 2874 × 1616 physical pixels for 1437 × 808 content points
at backing scale 2.0, confirming native Retina rendering in its current window.
This is separate from the owned fullscreen fixture above. No new combat FPS
result, complete clean build, account-safety result or new real CAPTCHA test
is claimed.
See [profile configuration and rollback](LAUNCHER-DISPLAY.md).
