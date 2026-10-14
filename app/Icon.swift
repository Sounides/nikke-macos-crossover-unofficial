// SPDX-License-Identifier: LGPL-2.1-or-later
// An original lettermark; no game artwork is bundled.
import AppKit
let image = NSImage(size: NSSize(width: 1024, height: 1024))
image.lockFocus()
let box = NSBezierPath(roundedRect: NSRect(x: 40, y: 40, width: 944, height: 944), xRadius: 190, yRadius: 190)
NSColor(calibratedRed: 0.075, green: 0.09, blue: 0.12, alpha: 1).setFill()
box.fill()
NSColor(calibratedRed: 0.90, green: 0.15, blue: 0.20, alpha: 1).setFill()
NSBezierPath(roundedRect: NSRect(x: 155, y: 135, width: 714, height: 22), xRadius: 11, yRadius: 11).fill()
let style = NSMutableParagraphStyle()
style.alignment = .center
func word(_ text: String, size: CGFloat, y: CGFloat, height: CGFloat) {
    let font = NSFont(name: "HelveticaNeue-CondensedBlack", size: size) ?? NSFont.boldSystemFont(ofSize: size)
    (text as NSString).draw(in: NSRect(x: 70, y: y, width: 884, height: height), withAttributes: [.font: font, .foregroundColor: NSColor.white, .paragraphStyle: style])
}
word("N", size: 600, y: 265, height: 660)
word("NIKKE", size: 130, y: 165, height: 165)
image.unlockFocus()
let bitmap = NSBitmapImageRep(data: image.tiffRepresentation!)!
try bitmap.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
