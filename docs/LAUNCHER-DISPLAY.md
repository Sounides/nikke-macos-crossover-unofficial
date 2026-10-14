# Launcher minimization and separate rendering resolutions

The default profile uses standard-DPI rendering for the official launcher and
its browser helpers while retaining native Retina rendering for the game.
This affects only the isolated Wine prefix; it changes no macOS display,
True Tone, Night Shift or refresh-rate preferences.

## Why the minimized box appeared

The tested launcher creates four separate layered, non-activating tool windows
for its shadow. When the main window minimized, these owned windows retained
their Windows visibility flag and moved around the small Windows icon
rectangle. Cocoa detached them from their minimized owner, leaving a shadow
box on the desktop even though the main launcher was gone.

The Mac driver now suppresses ordering a window onto the desktop while any
owner is minimized. Minimize/restore state changes synchronize same-process
owned windows as well. A tracking bit records which windows were suppressed;
restoration shows only those still marked visible in Windows and ready for
layered presentation. An explicitly hidden popup stays hidden. This does not
change the official launcher or replace its custom shadow implementation.

## How the resolution split works

Wine's Mac Retina coordinate setting is shared across this prefix. Giving
different processes inconsistent monitor coordinates can break positioning,
cross-process browser surfaces and input. The profile instead keeps
`RetinaMode=Y` and uses Wine's normal DPI virtualization:

| Setting | Value |
| --- | --- |
| `HKCU\Software\Wine\Mac Driver\RetinaMode` | `REG_SZ Y` |
| `HKCU\Control Panel\Desktop\LogPixels` | `REG_DWORD 192` |
| Wine's `dpiAwareness` image option for launcher/browser helpers | `REG_DWORD 0` |
| Original game's PerMonitorV2 awareness | Preserved |

The image options are under
`HKLM\Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options`
for `nikke_launcher.exe`, `intl_service.exe`, `tbs_browser.exe` and
`INTLWebViewHelper.exe`. They are Wine registry settings within this prefix.
No Debugger option, executable wrapper or vendor binary modification is used.

All browser helpers must use the same standard-DPI context. Configuring only
the launcher left its embedded browser at half width/height in the enlarged
window. Applying the helper options corrected the actual launcher capture.

A standard-DPI client uses one logical rendering pixel per Mac point, with
pixel doubling on the tested Retina display. The launcher therefore looks
larger and softer. The physical screenshot is still a Retina-sized image;
that does not mean the launcher is rendering twice as many detail pixels.
The DPI-aware game continues to use physical pixels and its existing DXMT
backend, movie fallback and fullscreen settings.

## Apply or undo the profile

New installations get this profile from `scripts/setup-prefix.sh`.
For an existing setup, close the game and launcher before rebuilding or
refreshing the prefix. Prefix setup stops only that prefix's Wine server
at the end so cached monitor DPI is discarded.

```bash
bash scripts/setup-prefix.sh "$NIKKE_WORK"
```

To return to the previous 96-DPI launcher behavior while keeping the game's
Retina mode enabled:

```bash
NIKKE_LAUNCHER_STANDARD_DPI=0 bash scripts/setup-prefix.sh "$NIKKE_WORK"
```

This removes the four image DPI overrides and sets this prefix's LogPixels
to 96. It restores this project's prior defaults, rather than an arbitrary
user-customized DPI configuration. As with any prefix/runtime refresh,
reapply the private DXMT installation if its files or overrides were reset.
Restart the launcher afterward. Neither command changes the display settings
of other Wine prefixes or macOS.

## Verification and limits

The old native module reproduced four orphan shadow windows in an owned
fixture. The revised module hid all of them on minimize and restored only
the root plus three still-visible popups; a fourth explicitly hidden popup
stayed hidden. Native geometry, not only Windows visibility flags, was checked.

The published account-free test passes with a 600 × 360 logical client
occupying 600 × 360 native points, plus API checks showing that all three
owned helper-image fixtures remain standard-DPI even when they request DPI
awareness:

```bash
python3 tests/windows.py --work-root "$NIKKE_WORK"
```

It creates a unique prefix under `window-test-prefix`, opens only owned fixture
windows, and reads native geometry only for the fixture PID. It requires a
logged-in macOS WindowServer session and Xcode's Swift compiler. No account
data is copied. It does not click or operate the installed launcher/game.

In the same 192-DPI/Retina configuration, an owned DXMT game fixture produced
a 3024 × 1964 backbuffer and screenshot in 1512 × 982 points. Its stripes
alternated every physical pixel, while the standard-DPI fixture showed pixel
doubling. The actual signed-in launcher was captured filling its full
1348 × 904 point window, with its browser helpers configured consistently.
Wine's render-size observer measured its final browser backbuffer at
1346 × 902 pixels, confirming lower-resolution source rendering within that
Retina-sized physical window. The final physical screenshot is 2696 × 1808.
DXMT raw-syscall, movie fallback and changing opaque GPU-video checks also
passed after installation of the native window fix.

The user confirmed that the shadow box disappears after minimizing the actual
launcher and that the game still renders at Retina resolution after Launch.
A native window-list check independently showed the minimized launcher and
all four shadow windows offscreen. The real game's Metal drawable measured
2874 × 1616 physical pixels for 1437 × 808 content points, with a backing
scale of 2.0. That is native Retina rendering for its current window, rather
than a new fullscreen panel-resolution measurement.

These fixtures do not establish new combat performance, behavior of every
browser dialog, future client/CEF releases or complete ACE functionality.
Prior gameplay evidence and the completed live display check are in
[test coverage](TESTING.md).
