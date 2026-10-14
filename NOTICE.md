# Attribution and provenance

The combined Wine patch contains LGPL-2.1-or-later Wine code and derived modifications. Copyright notices in the source files remain authoritative. The LGPL text is included in `LICENSE` and `LICENSES/LGPL-2.1.txt`. New scripts, documentation and app source in this package are also offered under LGPL-2.1-or-later. Dependency binaries are not included.

## Wine

Base: [Wine 11.18 source](https://github.com/wine-mirror/wine/tree/wine-11.18), SHA-256 recorded in `inputs.json`. All original source copyright notices are retained. Generated server files correspond to the included protocol change.

## Cross-process Mac rendering

The starting reference was the AI-assisted `winemac-crossprocess-child-core.patch` associated with [Wine bug 60263](https://bugs.winehq.org/show_bug.cgi?id=60263), attachment 82030, and [DXMT issue 141](https://github.com/3Shain/dxmt/issues/141#issuecomment-5477055980). Its header offers modifications under LGPL-2.1-or-later, preserves Wine/CodeWeavers context copyrights, and warns that DXMT does not accept AI-authored contributions. The implementation here adapts it to Wine 11.18, with subsequent geometry, input-origin and remote-surface edge-transform fixes. This repository is not a DXMT contribution.

## Dawn Winery kernel references

Compatibility work drew on [Dawn Winery's Wine fork](https://dawn.wine/dawn-winery/wine-dwproton) and its Wine 11.0-14 reference commit `b585905ec92032840e924e4e2a88382523e92ed3`. Relevant upstream patch authors include **mkrsym1 / Ziia Shi**, **shxrrydw**, and **Quitting**. Locally adapted/reference changes include:

| Upstream commit | Reference |
| --- | --- |
| `e332f9a4a3a8afbe4423bf77b260f3db08656af7` | DriverInit return-address tagging, mkrsym1 |
| `57817da4e9e946a134561ef3aa0df9ab1c27dc54` | DriverExtension service name, shxrrydw |
| `429496a0ddbc2a4301ff3cc4387a9f2d7ad16b99` | Locked MDL mapping lifetime, shxrrydw |
| `420eba7e67b1127f580eba63b1fc6c1f817719cc` | Server driver-module tracking, shxrrydw |
| `98d880af9a172bb3bc59bcc047a0751405f6c64f` | Driver-module registration, shxrrydw |
| `bbfa5f16b8122f93d4a60e0743be62f34b149ed4` | Loaded-driver query, shxrrydw |
| `77d384c342c3b1eacd5c955233c9efff5280cbe0` | Process-exit module cleanup, shxrrydw |
| `363bac18bb83ee63d709359b3b2d0612e36ff1b4` | UserMode thread-context thunk reference, shxrrydw |

The final patch preserves real failure results for unsupported operations and includes additional operational callbacks, System-context work items and raw-syscall context fixes. The earlier entry adapter and scoped GetProcAddress workaround are not included. Commit references describe provenance; they do not claim each original patch was applied unmodified.

## Video fallback

[Wine merge request 11398](https://gitlab.winehq.org/wine/wine/-/merge_requests/11398), **Stian Low**, supplies the seven-file `no_create_flags` configuration support. Its changes are included with minor whitespace cleanup. See Microsoft's [D3D11 device flags](https://learn.microsoft.com/en-us/windows/win32/api/d3d11/ne-d3d11-d3d11_create_device_flag) and [format support 2](https://learn.microsoft.com/en-us/windows/win32/api/d3d11/ne-d3d11-d3d11_format_support2) documentation for the API semantics.

## Build inputs

- [LLVM-MinGW](https://github.com/mstorsjo/llvm-mingw/releases/tag/20261006), Martin Storsjö and contributors.
- [GNU Bison](https://www.gnu.org/software/bison/), Free Software Foundation and contributors.
- [GStreamer](https://gstreamer.freedesktop.org/download/), GStreamer contributors and its codec dependencies.
- [CrossOver source](https://www.codeweavers.com/crossover/source), CodeWeavers and dependency authors; the recipe uses FreeType/GnuTLS headers from the recorded source archive and privately copied native libraries from the user's installation.
- [MoltenVK](https://github.com/KhronosGroup/MoltenVK), Khronos Group and contributors, through the locally supplied dependency library.

Each downloaded input and privately supplied library retains its own license. None of these dependency distributions is republished by this source package. NIKKE and its trademarks/artwork belong to their respective owners. The app builder uses an original lettermark and bundles no game artwork.


## DXMT interface

[DXMT](https://github.com/3Shain/dxmt), by 3Shain and contributors, supplies the separately obtained graphics backend. Its [configuration documentation](https://github.com/3Shain/dxmt/blob/main/docs/CUSTOMIZATION.md) describes Metal frame pacing. The new Wine bridge is this project's code; no DXMT source changes or binary redistribution are included. DXMT's contribution policy forbids AI-generated code contributions to that project. This repository does not submit such a contribution.


## Review-driven MDL and verification improvements

The allocation-wide MDL tracking, mapping-allocation failure handling, and
MDL/thread-context regression fixtures were adapted from
[kanata-dp/nikke-crossover-compat](https://github.com/kanata-dp/nikke-crossover-compat),
reference commit `8f3c77b131d068674e9b0c72c70595ab13fdaeed`, under its
[LGPL-2.1-or-later terms](https://github.com/kanata-dp/nikke-crossover-compat/blob/8f3c77b131d068674e9b0c72c70595ab13fdaeed/LICENSE).
These extend the shared DW-Proton MDL work credited above. Direct review and
adaptation occurred on October 14, 2026; this credit is additional to the
shared upstream ancestry, not a claim that earlier independent development
consulted that repository.

Its [September 26 update notes](https://github.com/kanata-dp/nikke-crossover-compat/blob/8f3c77b131d068674e9b0c72c70595ab13fdaeed/docs/UPDATE-2026-09-26.en.md)
document the three scoped CEF rendering switches used by the optional
verification repair. This package implements them in Wine process parameters;
it does not adopt the repository's official-service replacement wrapper.
Owned tests check target scoping, partial switch sets and duplicate avoidance.
The upstream project's remaining code and binaries are not bundled.
