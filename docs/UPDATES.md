# Launcher and game updates

Assessment: October 14, 2026, for the tested Wine 11.18 / DXMT setup.
**Routine official file updates are expected to work with the current layout,
but an actual official version-to-version upgrade has not been verified.**
Future launcher, browser, game or ACE versions can require new compatibility
work. This project does not freeze a client version or prevent mandatory updates.

## What survives a routine official update

The macOS app starts `C:\NIKKE\Launcher\nikke_launcher.exe` in the existing
isolated prefix each time. It does not embed a launcher copy or require a
particular launcher hash. The official launcher remains responsible for
downloading, verifying, replacing and starting its files.

Our rendering, loader, movie and kernel changes live in the Wine runtime,
outside `C:\NIKKE`. Game-specific registry settings live in the prefix's
registry. The runner reapplies the movie fallback on each fresh launch.
Private DXMT modules live in the runtime and Windows system directories;
the shader cache and codecs also live outside the official game directory.
An updater replacing only its own launcher/game files therefore does not
replace these compatibility components. An update that resets registry
values or changes system DLLs would need separate examination.

The launcher display profile also resides in the prefix registry: shared
Retina coordinates, LogPixels192 and standard-DPI options for the launcher
and its browser helper image names. Official replacements at those same names
retain the options. A renamed browser helper or a change to the game's DPI
manifest needs a new [display-profile check](LAUNCHER-DISPLAY.md).

The optional CAPTCHA option is implemented in Wine's process creation;
`intl_service.exe` is not replaced by a wrapper. Normal official replacements
of that executable do not require restoring an unofficial service file.

Native Dock names and icons belong to our macOS hosts, so official Windows
file replacements do not normally replace them. Internal host folder names
and identifiers remain stable even though the public labels now say
Unofficial Launcher for NIKKE and Unofficial NIKKE Game Host.

## Evidence and limits

| Check | Result |
| --- | --- |
| Fresh official launcher/game download | Previously completed in the working installation |
| Installed launcher and game destinations | Directories and executable files are writable on the tested Mac |
| Owned 32-bit launcher and update helper | Old launcher exits; helper replaces its file and restarts the new version |
| Owned 64-bit game replacement | The restarted launcher starts the new game fixture successfully |
| Environment and settings | Inherited sentinel, movie fallback and a game-specific DLL override survive the restart |
| Other files | Owned launcher/game preferences and sampled runtime hashes remain unchanged |
| Actual official version-to-version upgrade | Not verified; Computer Use denied access to NIKKE Launcher during this assessment |
| Future CEF/ACE/game behavior | Not established by the owned fixture or prior gameplay |

The fixture uses this repository's runner and a unique account-free prefix.
It contains only our own small programs, uses the current 32-bit launcher /
64-bit game layout, and relaunches with an unrelated working directory.
It does not reproduce the vendor's downloader, patch format, elevation flow,
authentication, integrity checks, browser, drivers or server responses.
It tests Windows file replacement and process lifetime, not a future release.

Run it with the built runtime and pinned toolchain:

```bash
python3 tests/updates.py --work-root "$NIKKE_WORK"
```

Compiled fixtures and logs remain under `update-tests/run-TIMESTAMP` in the
private work root. The test stops only its own prefix server. It does not
copy account data, change the installed game or rebuild the runtime.

## Update normally, then verify

1. Close the game normally. Open the macOS app and allow the official launcher
   to finish its update, including any self-restart. Complete any new terms
   or verification yourself. Do not interrupt a file replacement.
2. If the official launcher closes after updating without reappearing, open
   the macOS app again. The native starter exiting when its first launcher
   process exits is expected; the updater may continue in another process.
3. Allow the official game update to finish. Use Launch and verify sign-in,
   the changing title movie, the lobby and a short combat session.
4. Recheck display resolution and game graphics preferences if the update
   reset them. Repeat API tests when diagnosing a regression; they cannot
   substitute for checking the updated game itself.

For a private pre-update backup, first close this setup, stop its prefix
server and wait for it to exit. A prefix contains account material, so keep
the backup outside the source repository and never attach it to an issue:

```bash
WINEPREFIX="$NIKKE_WORK/custom-prefix" "$NIKKE_WORK/runtime/bin/wineserver" -k
WINEPREFIX="$NIKKE_WORK/custom-prefix" "$NIKKE_WORK/runtime/bin/wineserver" -w
ditto "$NIKKE_WORK/custom-prefix" \
  "$NIKKE_WORK/checkpoints/before-update-YYYYMMDD/custom-prefix"
```

Use a new backup directory and allow enough disk space. A backup does not
make an obsolete client acceptable to the server; use the official repair
or current installer to recover files required by the live service.

## Where a new version can break

- **Paths or executable names change.** The runner expects the official
  `C:\NIKKE` layout. Game host routing is specifically keyed to
  `C:\NIKKE\NIKKE\game\nikke.exe`; the DXMT and movie settings also use
  `nikke.exe`. A different layout needs code/configuration changes.
- **Launcher or CEF requirements change.** New window composition or Windows
  APIs can require further Wine fixes. The optional rendering switches are
  scoped to `intl_service.exe`; a renamed service will not receive them.
- **Downloader behavior changes.** The tested VersionService startup delay
  and silent miniloader arguments are version-specific observations. A new
  installer or updater may need fresh diagnosis.
- **Game, codec or ACE behavior changes.** New graphics, decoding or kernel
  requirements may exceed Wine's implementation. Prior protected startup
  and gameplay do not establish future support or complete ACE operation.

If an update stalls, first close this setup and retry the official launcher.
Inspect private logs locally and use the official launcher's repair option
if available. Do not manually mark downloads complete, edit manifests,
disable integrity checks or bypass mandatory updates. A fresh official
miniloader targeting the same directory is a recovery option to evaluate,
not an independently verified in-place update test here.

## Updates to this project or CrossOver

These are separate from NIKKE updates. The Wine patch and build inputs are
pinned; this package has no automatic updater for its own source/runtime.
A new patch can require rebuilding Wine, refreshing the prefix and
reapplying the private DXMT installation. Rebuild the native app when its
embedded `run.sh` changes; `install-app.py` refuses to overwrite an existing
app, so move it aside first.

CrossOver updates do not automatically replace the private dependency copies.
The tested CrossOver version remains the one in README.md. Re-copying newer
libraries or DXMT is a deliberate dependency upgrade that needs testing;
retain the known-working setup until the new one is validated.
