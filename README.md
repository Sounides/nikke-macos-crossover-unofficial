# Unofficial Launcher for NIKKE (CrossOver required)

**You must have your own authorized CrossOver installation to follow this build recipe.** It supplies the native dependency libraries and DXMT backend used by this setup. Obtain CrossOver from [CodeWeavers](https://www.codeweavers.com/crossover/download) and follow its license terms.

This project builds an isolated, patched **Wine 11.18 runtime** and native macOS launcher for **GODDESS OF VICTORY: NIKKE**, using dependencies copied from your CrossOver installation. The game runs in that custom runtime. The tested dependency provider is **CrossOver Preview 20261006, version 27.0.0.41069**; other versions are unverified.

This is an independent compatibility project, unaffiliated with and not endorsed by SHIFT UP, Proxima Beta, Level Infinite, CodeWeavers or the anti-cheat vendor. NIKKE and other product names belong to their respective owners. The official launcher and game retain their original names and files.

Tested on an **M3 Pro with 18 GB RAM, macOS 27.0.1**, PC client **152.8.13**, October 13–14, 2026.

**Using this unofficial compatibility setup could get your NIKKE account banned. A ban caused by this specific setup has not been confirmed; that does not establish account safety. Use it at your own risk.**

This project has no approval from the publisher or anti-cheat vendor. NIKKE publishes [sanctions for unauthorized programs](https://nikke-en.com/bannedlist20260904/); that notice does not identify this setup as permitted or prohibited. Review the [official terms](https://nikke-en.com/termsofservice/) yourself. This package is not a guarantee of legal compliance, complete anti-cheat functionality, or future compatibility.

## What works and what remains uncertain

The tested DXMT setup renders the official launcher without its white outline, downloads the game, signs in normally, plays the animated title movie, proceeds through the original protected startup, and reaches NA gameplay. Combat through chapter 2, including boss 2-12, was tested. Native fullscreen output was verified at **3024 × 1964 physical pixels** on the tested display.

DXMT is the selected game renderer; the launcher keeps Wine's built-in graphics. Recorded combat samples were approximately **56–60 FPS**, with stutters. **Constant 60 FPS has not been achieved or demonstrated.** Encounters differed, so the measurements are not controlled comparisons. See [display/performance evidence](docs/DISPLAY-PERFORMANCE.md) and [test coverage](docs/TESTING.md).

Wine's virtual kernel is incomplete. Successfully reaching gameplay does not prove that every ACE check or Windows security feature operates correctly. Long sessions, all chapters, multiplayer, other Macs, future client updates, and account-enforcement outcomes remain unverified.

## Publication contents

- A [39-file patch](patches/nikke-wine-11.18.patch) against pristine Wine 11.18, with exact source hashes.
- Pinned, checksum-verified build inputs and an isolated runtime/prefix recipe.
- A private DXMT installer with rollback, codec setup, official installer runner, and Swift app builder.
- Account-free [kernel/API regression tests](tests/kernel.py), GPU/movie smoke fixtures, documentation and [attribution](NOTICE.md).

Only source and documentation are distributed. Obtain the game and ACE through the official installer, and dependencies from their authorized sources. No game/ACE binaries, modified vendor executable, bootstrap adapter, game artwork, account prefix, credentials, tokens, account-bearing logs, Apple graphics libraries or CrossOver binaries are included. The GPTK experiment is not part of this package.

## Requirements

- **CrossOver installed before preparation or building.** Your own authorized installation must supply **x86_64** FreeType, GnuTLS, GMP and MoltenVK libraries, plus DXMT. The tested version is **CrossOver Preview 20261006, version 27.0.0.41069**. Other versions are unverified.
- Apple Silicon Mac with Rosetta available. The M3 Pro/macOS version above is the tested configuration.
- Xcode or Command Line Tools supplying Clang, Swift, the macOS SDK, make, flex and m4; Python **3.9+**.
- About 15 GB for build inputs/runtime/trees, plus space for the official game download. Compilation takes substantial time.

The scripts copy dependencies into this isolated setup; they do not modify CrossOver. CrossOver and its libraries are not bundled in this repository. Independently building those dependencies is outside the tested recipe. Downloaded source/toolchain/codec inputs are pinned in [inputs.json](inputs.json).

## Install CrossOver, then build the isolated runtime

Install CrossOver first and locate its native library directory. The example below uses the tested CrossOver Preview installation path; change it to your actual installation. Preparation requires that directory to contain the required libraries, and the later DXMT installation step also needs CrossOver's DXMT directory.

Run from this repository's root. Choose a permanent work directory **outside the repository and without spaces**. Build paths are embedded; moving the runtime requires rebuilding.

```bash
export NIKKE_WORK="$HOME/NIKKE-build"
export NIKKE_CACHE="$HOME/Downloads/nikke-build-inputs"
export NIKKE_DEPENDENCIES="/Applications/CrossOver Preview.app/Contents/SharedSupport/CrossOver/lib/x86_64"

python3 scripts/prepare.py --work-root "$NIKKE_WORK" \
  --cache "$NIKKE_CACHE" --dependency-libs "$NIKKE_DEPENDENCIES" --fetch
bash scripts/build.sh "$NIKKE_WORK"
bash scripts/setup-prefix.sh "$NIKKE_WORK"
```

Use the actual donor path on your Mac. Preparation refuses an existing source tree, checks all downloads and patched-source hashes, and extracts GStreamer packages locally. It does not install codecs system-wide. Stop if an input checksum changes. Builds use eight jobs; set `NIKKE_BUILD_JOBS=4` if necessary. Private logs remain under the work root.

Prefix setup now uses **standard-DPI rendering for the launcher and its browser helpers**, while the game keeps its native Retina mode. The launcher appears larger and softer on the tested display. Close this setup before refreshing its prefix. See [launcher display settings and rollback](docs/LAUNCHER-DISPLAY.md) for the profile and its opt-out.

Download the PC installer from the [official NIKKE site](https://nikke-en.com/), then:

```bash
bash scripts/run.sh "$NIKKE_WORK" install "/absolute/path/to/nikkeminiloader.exe"
```

The tested miniloader supports `/S /Silent` and installs its launcher into `C:\NIKKE`. If a future installer changes behavior, run the official installer interactively in this isolated prefix and choose that directory. Accept terms yourself. Sign in and complete any verification directly in the official launcher. Never put passwords, codes or tokens into scripts or issues.

Close the launcher before installing the DXMT dependencies:

```bash
python3 scripts/install-dxmt.py --work-root "$NIKKE_WORK" \
  --donor "/Applications/CrossOver Preview.app/Contents/SharedSupport/CrossOver/lib/dxmt"
bash scripts/run.sh "$NIKKE_WORK" launch
```

Use the launcher's **Launch** button and your account's server. The game runs its original executable entry and installed ACE components. The runner selects DXMT only for `nikke.exe`, uses a private shader cache and requests 60 FPS pacing. Movies use the tested software-decoding fallback. Choose **FullScreen**, **60 FPS**, then **Save** in the game's Graphics menu for native output; verify other displays separately.

DXMT installation prints a rollback checkpoint. See [implementation and rollback](docs/IMPLEMENTATION.md). Reapply the private DXMT step after a runtime rebuild if needed.

## Native Applications app and Dock icons

After installing the official launcher:

```bash
python3 scripts/install-app.py --work-root "$NIKKE_WORK"
```

This creates `/Applications/Unofficial Launcher for NIKKE.app`, a native starter with an original lettermark icon and a reference to your local setup. Its runtime/account data stays in the work root. The visible Wine hosts use the Dock labels **Unofficial Launcher for NIKKE** and **Unofficial NIKKE Game Host** and share the app icon. Double-click the app to open the official launcher. Internal Wine bundle folders and official Windows executable names remain stable for routing; the labels describe our macOS hosts.

Optionally provide your own authorized image with `--icon "/absolute/path/to/icon.png"`. Game artwork is not distributed. If Applications is not writable, add `--destination "$HOME/Applications/Unofficial Launcher for NIKKE.app"`. Move an existing app aside before rebuilding; the installer refuses to overwrite it. These path-specific generated apps are not portable releases.

For an existing app's icon synchronization:

```bash
python3 scripts/set-dock-icons.py --work-root "$NIKKE_WORK" \
  --icon "/Applications/Unofficial Launcher for NIKKE.app/Contents/Resources/NIKKE.icns"
```

Restart the launcher/game afterward. Close them normally; for this setup's stuck processes use `bash scripts/run.sh "$NIKKE_WORK" stop`.

The native window patch also hides the launcher's owned shadow windows when
it minimizes, then restores only those still visible in Windows. This fixes
the leftover shadow box, confirmed in the real launcher after minimize/restore.
The same setup retains native Retina rendering in the real game.
See [minimization and rendering-resolution details](docs/LAUNCHER-DISPLAY.md).

## Official launcher and game updates

The app always starts the official launcher installed in the same prefix.
Routine official file updates are expected to preserve our separate Wine,
DXMT and codec changes. An owned 32-bit launcher/helper replacement-and-restart
test successfully launched an updated 64-bit game fixture with its settings
preserved. **An actual official version-to-version update has not been verified.**
Future launcher, CEF or ACE changes may break compatibility. See the
[update assessment, verification and recovery steps](docs/UPDATES.md), including
the separate procedure for updating this project's runtime or embedded runner.

## Optional blank-CAPTCHA repair

If the official verification popup is white, close this setup and relaunch:

```bash
NIKKE_CEF_SOFTWARE=1 bash scripts/run.sh "$NIKKE_WORK" launch
```

This adds three rendering switches only when Wine starts `intl_service.exe`: `--disable-gpu`, `--disable-gpu-compositing`, and `--in-process-gpu`. It preserves the official executable, normal authentication, certificate validation and browser sandbox. It does not solve or skip the CAPTCHA. The switch combination displayed verification successfully in a separate host; the DXMT integration passes seven owned subprocess tests, but a new real CAPTCHA in this DXMT build has not been independently revalidated. The option is off by default.

## Validate the source and APIs

```bash
python3 scripts/check-package.py
python3 scripts/verify-patch.py "/path/to/wine-11.18.tar.gz"
python3 tests/kernel.py --work-root "$NIKKE_WORK"
python3 tests/updates.py --work-root "$NIKKE_WORK"
python3 tests/windows.py --work-root "$NIKKE_WORK"
python3 tests/smoke.py --work-root "$NIKKE_WORK" \
  --video "/path/to/your-changing-h264-video.mp4" --dxmt
```

Kernel/API tests use a separate account-free `kernel-test-prefix`. They cover allocation-wide MDL references, process exit status, thread context, kernel threads/work items, scoped verification switches and valid/invalid instruction handling. GPU smoke tests use the configured prefix and their own fixture names; close the game first. Test logs and compiled fixtures remain private. Passing tests does not establish publisher approval or full Windows/ACE enforcement.

## License, provenance and publishing

Wine modifications and new package code are **LGPL-2.1-or-later**. Existing copyright notices remain intact; [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) document shared upstream work and the new adaptations from kanata-dp/nikke-crossover-compat. Substantial AI assistance was used. This is not a contribution to DXMT, whose contribution policy rejects AI-generated code.

The publication check rejects unmanifested files, binaries, symlinks, local user paths and common credential patterns. It cannot guarantee legal, licensing, security or account safety. Keep only this source directory in your GitHub repository; never upload your work root or dependency/game files.

No GitHub repository is created or published by the build tools.
