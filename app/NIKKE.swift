// SPDX-License-Identifier: LGPL-2.1-or-later
import AppKit

final class LauncherDelegate: NSObject, NSApplicationDelegate {
    private var child: Process?
    private var workRoot: URL?

    private func alert(_ detail: String) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        let alert = NSAlert()
        alert.messageText = "Unofficial Launcher for NIKKE could not start"
        alert.informativeText = detail
        alert.addButton(withTitle: "OK")
        alert.runModal()
        NSApp.terminate(nil)
    }

    private func showExistingLauncher() -> Bool {
        guard let root = workRoot else { return false }
        let expected = root.appendingPathComponent("runtime/lib/wine/x86_64-unix/NIKKE Launcher.app/Contents/MacOS/wine")
        for app in NSRunningApplication.runningApplications(withBundleIdentifier: "org.winehq.wine") {
            if app.executableURL?.standardizedFileURL == expected.standardizedFileURL {
                app.activate(options: [])
                return true
            }
        }
        return false
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        guard let resources = Bundle.main.resourceURL,
              let data = try? Data(contentsOf: resources.appendingPathComponent("Setup.plist")),
              let settings = try? PropertyListSerialization.propertyList(from: data, format: nil) as? [String: String],
              let path = settings["WorkRoot"] else {
            alert("Rebuild this app with scripts/install-app.py and the location of your NIKKE setup.")
            return
        }
        workRoot = URL(fileURLWithPath: path, isDirectory: true)
        if showExistingLauncher() { NSApp.terminate(nil); return }
        let required = ["runtime/bin/wine", "custom-prefix/drive_c/NIKKE/Launcher/nikke_launcher.exe"]
        guard required.allSatisfy({ FileManager.default.fileExists(atPath: path + "/" + $0) }) else {
            alert("The Wine runtime or official launcher is missing at:\n\(path)\n\nKeep the setup at its installed location, or rebuild the app for its new location.")
            return
        }
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = [resources.appendingPathComponent("run.sh").path, path, "launch"]
        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice
        process.terminationHandler = { process in
            DispatchQueue.main.async {
                if process.terminationStatus != 0 {
                    self.alert("The launcher exited with status \(process.terminationStatus). Local diagnostics are in the setup's logs folder; review them privately before sharing.")
                } else {
                    NSApp.terminate(nil)
                }
            }
        }
        do { try process.run(); child = process }
        catch { alert(error.localizedDescription) }
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        _ = showExistingLauncher()
        return false
    }
}

let app = NSApplication.shared
let delegate = LauncherDelegate()
app.setActivationPolicy(.accessory)
app.delegate = delegate
app.run()
