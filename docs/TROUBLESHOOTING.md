# Troubleshooting

**A shadow box remains after minimizing:** use the current native driver patch,
then restart this setup. It suppresses owned shadow windows while their owner
is iconic. The source change must be rebuilt; changing registry DPI alone does
not fix the shadows. See [launcher display details](LAUNCHER-DISPLAY.md).

**Only a quarter of the enlarged launcher contains content:** make sure the
standard-DPI profile includes tbs_browser.exe, intl_service.exe and
INTLWebViewHelper.exe, then restart all processes in this prefix. Applying
only the nikke_launcher.exe option leaves the cross-process browser layout
inconsistent. Keep the game's native Retina mode enabled.

**Preparation fails a checksum:** compare the pinned URL and version in `inputs.json`. A different source archive or regenerated upstream download may have different bytes. Keep the checksum failure visible; establish provenance before updating the manifest.

**Preparation is interrupted:** it may leave partially extracted source or packages. Choose another fresh work root. Do not apply the combined patch twice or reuse an unrelated prefix.

**Missing dependency library:** `--dependency-libs` must point at a directory containing all four x86_64 libraries listed in the README. This recipe uses the tested CrossOver donor. ARM-only Homebrew libraries cannot replace x86_64 native dependencies in this Rosetta runtime.

**Build fails:** inspect the last compiler error in `logs/bison-build.log`, `logs/wine-build.log` or `logs/media-build.log`. Ensure Xcode's active SDK and tools work with `xcrun --find clang`, `xcrun --find swiftc` and `xcrun --sdk macosx --show-sdk-path`. Use a work path without spaces. The scripts intentionally stop on an error.

**App cannot start:** the generated app references its selected work root. Check that `runtime/bin/wine` and `custom-prefix/drive_c/NIKKE/Launcher/nikke_launcher.exe` exist there. Launch from `scripts/run.sh` for a more direct diagnostic. Move an old app aside before rebuilding; installation refuses to overwrite an existing bundle.

**Launcher is blank or outlined:** verify that the custom native Mac driver is installed, renderer is `vulkan`, and all Wine modules and wineserver come from the same patched build. Close the launcher normally and reopen it after module replacement. Running processes keep their old mapped code.

**Installer stays at zero:** the tested official miniloader recovered on its retry after VersionService initialization. Confirm the downloader-specific delay patch is present. Keep the official network/authentication behavior and inspect errors locally; a future service or installer change may need new diagnosis.

**Movie is black:** verify both GStreamer package versions, the filtered codec directory, both winegstreamer registrations, and the `nikke.exe` `no_create_flags=0x800` setting. Successful audio alone does not prove video rendering. The title movie is the verified case.

**ACE or protected startup fails:** use the official launcher and the original game files. Check that the native ntdll includes the macOS SIGSYS/TEB fix and the server matches the custom DLLs. Report the client/version and sanitized error code. A later ACE update can introduce an unsupported API; successful initialization in this snapshot is not a promise about future revisions.

**A process is stuck:** first close normally. `scripts/run.sh WORK_ROOT stop` targets only the named NIKKE game/launcher processes in the selected prefix. It does not kill all Wine processes or unrelated bottles.

**Sharing diagnostics:** report versions, a minimal reproduction, and a sanitized error code. Do not upload the prefix, full game logs, launcher command lines, user profile, or screenshots containing account identifiers. Review logs manually before sharing.


## Blank game view after a live display refresh change

Changing between 60 Hz and ProMotion during a running DXMT session produced a persistent blank game view in the final comparison. Restart the selected isolated prefix, then use the official launcher after changing display modes. A game-only restart was insufficient in this test; cold prefix startup recovered rendering. The app does not automate global display changes. Normal cold startup at ProMotion remains the tested route; do not count a blank view's presentation timestamps as gameplay FPS.


**Fatal error in GC / SuspendThread loop failed:** one normal startup after the display-mode experiment hit this garbage-collector error. A game-only retry through the signed-in official launcher reached the NA title and lobby. This is not evidence of an ACE rejection or a confirmed permanent fix. Preserve a sanitized error report if it recurs; do not suppress failed thread-suspension or thread-context calls.


## White verification/CAPTCHA popup

Close the game and launcher, then use
`NIKKE_CEF_SOFTWARE=1 bash scripts/run.sh "$NIKKE_WORK" launch`.
The option scopes three CEF rendering switches to intl_service.exe; complete
verification yourself. It does not disable certificate checks or the sandbox.
Omit the environment variable on the next restart to restore the default.
Its DXMT integration has owned subprocess coverage; actual reauthentication
with a newly issued CAPTCHA still needs case-by-case visual verification.
