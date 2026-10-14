// SPDX-License-Identifier: LGPL-2.1-or-later
// Read geometry for only the owned fixture PID; no pixels, input or window titles.
import AppKit
import CoreGraphics

_ = NSApplication.shared
guard CommandLine.arguments.count == 2, let pid = Int(CommandLine.arguments[1]), pid > 0 else {
    fputs("Provide the owned fixture's native PID.\n", stderr)
    exit(2)
}
guard let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] else {
    fputs("Unable to read native window metadata.\n", stderr)
    exit(3)
}
let owned = windows.filter { ($0[kCGWindowOwnerPID as String] as? NSNumber)?.intValue == pid }
let output = owned.map { window -> [String: Any] in
    ["id": window[kCGWindowNumber as String] ?? 0,
     "bounds": window[kCGWindowBounds as String] ?? [:],
     "layer": window[kCGWindowLayer as String] ?? 0]
}
let data = try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys])
print(String(data: data, encoding: .utf8)!)
