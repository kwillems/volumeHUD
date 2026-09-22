#!/usr/bin/env python3
# Definitieve patch voor een SCHONE originele volumeHUD v3.3.3-bronmap.
# Bevat alleen de bewezen werkende functies; Automatic Brightness is bewust NIET opgenomen.
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
SRC = ROOT / "volumeHUD"

BRIGHTNESS = SRC / "BrightnessMonitor.swift"
MEDIA = SRC / "MediaKeyInterceptor.swift"
HUD = SRC / "HUDController.swift"
APP = SRC / "VolumeHUDApp.swift"
ABOUT = SRC / "AboutView.swift"
TRUE_TONE = SRC / "TrueToneController.swift"
RESOURCES = SRC / "Resources"
MENU_ICON = RESOURCES / "MenuBarIcon.svg"

BACKUP_DIR = ROOT / "patch-backup-original"

FINAL_MENU_ICON_SVG = r'''<svg xmlns="http://www.w3.org/2000/svg" width="44" height="22" viewBox="0 0 44 22">
<g fill="#000">
<path d="M1.2 6.9h3.1l3.7-3.2c.65-.56 1.65-.10 1.65.76v10.9c0 .86-1 1.32-1.65.76l-3.7-3.2H1.2c-.66 0-1.2-.54-1.2-1.2V8.1c0-.66.54-1.2 1.2-1.2z"/>
<path d="M11.3 7.0a.8.8 0 0 1 1.13.03 4.4 4.4 0 0 1 0 6.3.8.8 0 1 1-1.16-1.1 2.8 2.8 0 0 0 0-4.1.8.8 0 0 1 .03-1.13z"/>
<path d="M13.7 5.0a.8.8 0 0 1 1.13.03 7.3 7.3 0 0 1 0 10.3.8.8 0 1 1-1.16-1.1 5.7 5.7 0 0 0 0-8.1.8.8 0 0 1 .03-1.13z"/>
<path fill-rule="evenodd" d="M22.2 4.2c0-.83.67-1.5 1.5-1.5h15.6c.83 0 1.5.67 1.5 1.5v8.2c0 .83-.67 1.5-1.5 1.5h-6.1v1.25h2.45a.75.75 0 0 1 0 1.5h-8.3a.75.75 0 0 1 0-1.5h2.45V13.9h-6.1c-.83 0-1.5-.67-1.5-1.5V4.2zm1.7.2v7.8h15.2V4.4H23.9z"/>
<rect x="1.5" y="17.9" width="4.6" height="3.0" rx=".8"/>
<rect x="7.55" y="17.9" width="4.6" height="3.0" rx=".8"/>
<rect x="13.6" y="17.9" width="4.6" height="3.0" rx=".8"/>
<rect x="19.65" y="17.9" width="4.6" height="3.0" rx=".8"/>
<rect x="25.7" y="17.9" width="4.6" height="3.0" rx=".8"/>
<rect x="31.75" y="17.9" width="4.6" height="3.0" rx=".8" opacity=".32"/>
<rect x="37.8" y="17.9" width="4.6" height="3.0" rx=".8" opacity=".32"/>
</g></svg>'''

FINAL_BRIGHTNESS_SELECTOR = r'''    /// Returns the preferred display for brightness control.
    ///
    /// Do not rely on DisplayServicesCanChangeBrightness for external Apple displays.
    /// Some Studio Display/macOS combinations can still be read/written correctly.
    private func getBrightnessDisplayID() -> CGDirectDisplayID? {
        guard let getBrightness = getBrightnessFunc else {
            return nil
        }

        var displayCount: UInt32 = 0
        guard CGGetActiveDisplayList(0, nil, &displayCount) == .success, displayCount > 0 else {
            return nil
        }

        var activeDisplays = [CGDirectDisplayID](repeating: 0, count: Int(displayCount))
        guard CGGetActiveDisplayList(displayCount, &activeDisplays, &displayCount) == .success else {
            return nil
        }

        let displays = Array(activeDisplays.prefix(Int(displayCount)))

        func canReadBrightness(_ display: CGDirectDisplayID) -> Bool {
            var brightness: Float = 0.0
            return getBrightness(display, &brightness) == KERN_SUCCESS
        }

        let readableDisplays = displays.filter(canReadBrightness)
        let mainDisplay = CGMainDisplayID()

        // First choice: external Apple display (Studio Display / Pro Display XDR).
        // Apple's display vendor ID is 0x0610.
        if let appleExternal = readableDisplays.first(where: {
            CGDisplayIsBuiltin($0) == 0 && CGDisplayVendorNumber($0) == 0x0610
        }) {
            return appleExternal
        }

        // Next: readable external main display.
        if let primaryExternal = readableDisplays.first(where: {
            $0 == mainDisplay && CGDisplayIsBuiltin($0) == 0
        }) {
            return primaryExternal
        }

        // Then any readable external display.
        if let external = readableDisplays.first(where: {
            CGDisplayIsBuiltin($0) == 0
        }) {
            return external
        }

        // Finally preserve built-in behaviour.
        if let primary = readableDisplays.first(where: { $0 == mainDisplay }) {
            return primary
        }

        return readableDisplays.first
    }'''

FINAL_MONITOR_GET_CURRENT = r'''    private func getCurrentBrightness() -> Float? {
        // Use cached DisplayServices function pointers.
        guard let getBrightness = getBrightnessFunc else {
            logger.error("getCurrentBrightness: Function pointers not available.")
            return nil
        }

        guard let targetDisplay = getBrightnessDisplayID() else {
            if !hasLoggedNoDisplayDetected {
                logger.warning("getCurrentBrightness: No DisplayServices-capable display detected.")
                hasLoggedNoDisplayDetected = true
            }
            return nil
        }

        var brightness: Float = 0.0
        let result = getBrightness(targetDisplay, &brightness)
        if result == KERN_SUCCESS {
            return brightness
        }

        logger.error("getCurrentBrightness: getBrightness failed with result \(result)")
        return nil
    }'''

FINAL_SET_BRIGHTNESS = r'''    /// Set the brightness (0.0 to 1.0).
    ///
    /// For Studio Display, do not immediately read the value back:
    /// the hardware update can be asynchronous. A successful DisplayServices
    /// setter call is enough; BrightnessMonitor will observe the real value later.
    private func setBrightness(_ brightness: Float, displayID: CGDirectDisplayID) -> Float? {
        guard let setBrightness = setBrightnessFunc else {
            return nil
        }

        let clampedBrightness = max(0.0, min(1.0, brightness))
        let result = setBrightness(displayID, clampedBrightness)

        guard result == KERN_SUCCESS else {
            logger.error("DisplayServicesSetBrightness failed with result \(result)")
            return nil
        }

        // Mirror the standalone ds-up/ds-down test that works on Studio Display.
        if let handle = dlopen(
            "/System/Library/PrivateFrameworks/DisplayServices.framework/DisplayServices",
            RTLD_NOW
        ), let ptr = dlsym(handle, "DisplayServicesBrightnessChanged") {
            let brightnessChanged = unsafeBitCast(
                ptr,
                to: (@convention(c) (CGDirectDisplayID, Double) -> Void).self
            )
            brightnessChanged(displayID, Double(clampedBrightness))
            dlclose(handle)
        }

        // Return the requested value so adjustBrightness() keeps intercepting.
        return clampedBrightness
    }'''

FINAL_ADJUST_BRIGHTNESS = r'''    /// Adjust brightness by delta and show HUD. Verifies the change worked.
    private func adjustBrightness(delta: Float) {
        // Check if DisplayServices is available.
        guard setBrightnessFunc != nil else {
            disableBrightnessInterception(reason: "DisplayServices not available")
            return
        }

        // Get preferred DisplayServices-capable display.
        guard let displayID = getBrightnessDisplayID() else {
            disableBrightnessInterception(reason: "no DisplayServices-capable display found")
            return
        }

        guard let currentBrightness = getCurrentBrightness(displayID: displayID) else {
            disableBrightnessInterception(reason: "cannot read brightness")
            return
        }

        // Calculate expected new brightness with quantization.
        let steps = 1.0 / abs(delta)
        var expectedBrightness = currentBrightness + delta
        expectedBrightness = round(expectedBrightness * steps) / steps
        expectedBrightness = max(0.0, min(1.0, expectedBrightness))

        // Check if we're at a boundary.
        let atBoundary = (currentBrightness <= 0.001 && delta < 0) || (currentBrightness >= 0.999 && delta > 0)

        // Set the brightness and get the requested result.
        guard let actualBrightness = setBrightness(expectedBrightness, displayID: displayID) else {
            disableBrightnessInterception(reason: "cannot set brightness")
            return
        }

        // Verify the request (if not at a boundary).
        if !atBoundary {
            let brightnessChanged = abs(actualBrightness - currentBrightness) > 0.001
            if !brightnessChanged {
                disableBrightnessInterception(reason: "brightness change did not take effect")
                // Still show HUD with current state even though we're disabling.
            }
        }

        // Quantize for display.
        let quantizedBrightness = round(actualBrightness * 16.0) / 16.0

        // Show our HUD (only if brightness feature is enabled).
        if brightnessHUDEnabled {
            hudController?.showBrightnessHUD(brightness: quantizedBrightness)
        }

        logger.debug("Brightness adjusted: \(Int(quantizedBrightness * 100))%")
    }'''

FINAL_EVENT_CALLBACK = r'''    /// Static callback for the HID-level CGEvent tap. Bridges to instance method.
    private static let eventTapCallback: CGEventTapCallBack = { _, type, cgEvent, userInfo in
        guard let userInfo else {
            return Unmanaged.passRetained(cgEvent)
        }

        let interceptor = Unmanaged<MediaKeyInterceptor>.fromOpaque(userInfo).takeUnretainedValue()

        if type == .tapDisabledByTimeout || type == .tapDisabledByUserInput {
            if let tap = interceptor.eventTap {
                CGEvent.tapEnable(tap: tap, enable: true)
            }
            if let tap = interceptor.sessionEventTap {
                CGEvent.tapEnable(tap: tap, enable: true)
            }
            return Unmanaged.passRetained(cgEvent)
        }

        guard type.rawValue == 14 else {
            return Unmanaged.passRetained(cgEvent)
        }

        return interceptor.handleEvent(cgEvent)
    }'''

FINAL_SESSION_CALLBACK = r'''
    /// Annotated-session callback used for synthetic media-key events.
    ///
    /// Stream Deck media actions can arrive too late in the event pipeline for
    /// the HID tap. This callback handles brightness, volume and mute.
    /// Duplicate synthetic key-downs emitted within 50 ms are consumed once.
    private static let sessionEventTapCallback: CGEventTapCallBack = { _, type, cgEvent, userInfo in
        guard let userInfo else {
            return Unmanaged.passRetained(cgEvent)
        }

        let interceptor = Unmanaged<MediaKeyInterceptor>.fromOpaque(userInfo).takeUnretainedValue()

        if type == .tapDisabledByTimeout || type == .tapDisabledByUserInput {
            if let tap = interceptor.sessionEventTap {
                CGEvent.tapEnable(tap: tap, enable: true)
            }
            return Unmanaged.passRetained(cgEvent)
        }

        guard type.rawValue == 14,
              let nsEvent = NSEvent(cgEvent: cgEvent),
              nsEvent.type == .systemDefined,
              nsEvent.subtype.rawValue == 8
        else {
            return Unmanaged.passRetained(cgEvent)
        }

        let data1 = nsEvent.data1
        let keyCode = (data1 & 0xFFFF_0000) >> 16
        let keyFlags = data1 & 0x0000_FFFF
        let keyState = (keyFlags & 0xFF00) >> 8

        // Only handle media-key down events that volumeHUD understands.
        guard keyState == 0x0A,
              NXKeyType(rawValue: keyCode) != nil
        else {
            return Unmanaged.passRetained(cgEvent)
        }

        let now = ProcessInfo.processInfo.systemUptime
        if interceptor.lastAnnotatedMediaKeyCode == keyCode,
           now - interceptor.lastAnnotatedMediaKeyTime <
               interceptor.annotatedMediaKeyDeduplicationWindow
        {
            interceptor.logger.debug(
                "Ignoring duplicate annotated-session media event: keyCode=\(keyCode)"
            )
            // Consume the duplicate so macOS does not handle it either.
            return nil
        }

        interceptor.lastAnnotatedMediaKeyCode = keyCode
        interceptor.lastAnnotatedMediaKeyTime = now

        interceptor.logger.debug(
            "Annotated-session media event detected: keyCode=\(keyCode)"
        )

        return interceptor.handleEvent(cgEvent)
    }
'''

FINAL_START = r'''    func start() -> Bool {
        guard !isRunning else {
            logger.debug("MediaKeyInterceptor already running.")
            return true
        }

        // Reset fallback states on start (allows re-testing each app launch).
        volumeInterceptionWorking = true
        brightnessInterceptionWorking = true
        volumeControlState = nil

        // Check accessibility permissions first.
        guard AXIsProcessTrusted() else {
            logger.warning("MediaKeyInterceptor: Accessibility permissions not granted. Cannot intercept media keys.")
            return false
        }

        let systemDefinedMask: CGEventMask = 1 << 14 // NX_SYSDEFINED = 14
        let userInfo = Unmanaged.passUnretained(self).toOpaque()

        guard
            let tap = CGEvent.tapCreate(
                tap: .cghidEventTap,
                place: .headInsertEventTap,
                options: .defaultTap,
                eventsOfInterest: systemDefinedMask,
                callback: MediaKeyInterceptor.eventTapCallback,
                userInfo: userInfo,
            ) else
        {
            logger.error("MediaKeyInterceptor: Failed to create CGEvent tap. Check accessibility permissions.")
            return false
        }

        eventTap = tap
        runLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)

        if let source = runLoopSource {
            CFRunLoopAddSource(CFRunLoopGetMain(), source, .commonModes)
            CGEvent.tapEnable(tap: tap, enable: true)
            isRunning = true

            // A second active tap at annotated-session level catches synthetic
            // NX_SYSDEFINED media events generated by software such as Stream Deck.
            if let sessionTap = CGEvent.tapCreate(
                tap: .cgAnnotatedSessionEventTap,
                place: .headInsertEventTap,
                options: .defaultTap,
                eventsOfInterest: systemDefinedMask,
                callback: MediaKeyInterceptor.sessionEventTapCallback,
                userInfo: userInfo
            ) {
                sessionEventTap = sessionTap
                sessionRunLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, sessionTap, 0)

                if let sessionSource = sessionRunLoopSource {
                    CFRunLoopAddSource(CFRunLoopGetMain(), sessionSource, .commonModes)
                    CGEvent.tapEnable(tap: sessionTap, enable: true)
                    logger.debug("Started annotated-session media-key interception.")
                } else {
                    logger.warning("MediaKeyInterceptor: Failed to create annotated-session event-tap run loop source.")
                    sessionEventTap = nil
                }
            } else {
                logger.warning("MediaKeyInterceptor: Failed to create annotated-session event tap; synthetic media keys may pass through.")
            }

            startDeviceChangeMonitoring()
            logger.debug("Started intercepting media keys.")
            return true
        } else {
            logger.error("MediaKeyInterceptor: Failed to create run loop source.")
            eventTap = nil
            return false
        }
    }'''

FINAL_STOP = r'''    func stop() {
        guard isRunning else { return }

        stopDeviceChangeMonitoring()

        if let tap = eventTap {
            CGEvent.tapEnable(tap: tap, enable: false)
        }

        if let source = runLoopSource {
            CFRunLoopRemoveSource(CFRunLoopGetMain(), source, .commonModes)
        }

        if let tap = sessionEventTap {
            CGEvent.tapEnable(tap: tap, enable: false)
        }

        if let source = sessionRunLoopSource {
            CFRunLoopRemoveSource(CFRunLoopGetMain(), source, .commonModes)
        }

        sessionRunLoopSource = nil
        sessionEventTap = nil
        runLoopSource = nil
        eventTap = nil
        isRunning = false

        if let handle = displayServicesHandle {
            dlclose(handle)
            displayServicesHandle = nil
        }

        logger.debug("Stopped intercepting media keys.")
    }'''

FINAL_HUD_HELPER = r'''
    /// Chooses the screen on which the brightness HUD should appear.
    /// Prefer Apple Studio Display, then the primary external display, then any external display,
    /// and finally the built-in panel.
    private func getPreferredBrightnessScreen() -> NSScreen? {
        if let studioDisplay = NSScreen.screens.first(where: {
            $0.localizedName.localizedCaseInsensitiveContains("Studio Display")
        }) {
            return studioDisplay
        }

        let mainDisplayID = CGMainDisplayID()

        if let primaryExternal = NSScreen.screens.first(where: { screen in
            guard let screenNumber = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber else {
                return false
            }
            let displayID = CGDirectDisplayID(screenNumber.uint32Value)
            return displayID == mainDisplayID && CGDisplayIsBuiltin(displayID) == 0
        }) {
            return primaryExternal
        }

        if let external = NSScreen.screens.first(where: { screen in
            guard let screenNumber = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber else {
                return false
            }
            return CGDisplayIsBuiltin(CGDirectDisplayID(screenNumber.uint32Value)) == 0
        }) {
            return external
        }

        return getBuiltinScreen()
    }
'''



FINAL_TRUE_TONE_CONTROLLER = r'''//
//  TrueToneController.swift
//  volumeHUD
//
//  True Tone control through Apple's private CoreBrightness framework.
//

import Combine
import Darwin
import Foundation
import ObjectiveC

final class TrueToneController: ObservableObject {
    @Published private(set) var isEnabled = false
    @Published private(set) var isAvailable = false

    private var frameworkHandle: UnsafeMutableRawPointer?
    private var client: NSObject?

    init() {
        loadClient()
        refresh()
    }

    private func loadClient() {
        let path =
            "/System/Library/PrivateFrameworks/CoreBrightness.framework/CoreBrightness"

        frameworkHandle = dlopen(path, RTLD_NOW | RTLD_LOCAL)

        guard frameworkHandle != nil,
              let clientType = NSClassFromString("CBTrueToneClient") as? NSObject.Type
        else {
            isAvailable = false
            return
        }

        client = clientType.init()
    }

    func refresh() {
        guard let client else {
            isAvailable = false
            isEnabled = false
            return
        }

        let supported = callBool(client, selectorName: "supported")
        let available = callBool(client, selectorName: "available")

        isAvailable = supported && available
        isEnabled = isAvailable
            ? callBool(client, selectorName: "enabled")
            : false
    }

    @discardableResult
    func setEnabled(_ enabled: Bool) -> Bool {
        guard isAvailable, let client else {
            return false
        }

        let result = callBool(
            client,
            selectorName: "setEnabled:",
            argument: enabled
        )

        refresh()
        return result
    }

    private func callBool(
        _ object: NSObject,
        selectorName: String
    ) -> Bool {
        let selector = NSSelectorFromString(selectorName)

        guard let method = class_getInstanceMethod(type(of: object), selector)
        else {
            return false
        }

        typealias Function = @convention(c) (AnyObject, Selector) -> Bool
        let implementation = method_getImplementation(method)
        let function = unsafeBitCast(implementation, to: Function.self)

        return function(object, selector)
    }

    private func callBool(
        _ object: NSObject,
        selectorName: String,
        argument: Bool
    ) -> Bool {
        let selector = NSSelectorFromString(selectorName)

        guard let method = class_getInstanceMethod(type(of: object), selector)
        else {
            return false
        }

        typealias Function = @convention(c) (AnyObject, Selector, Bool) -> Bool
        let implementation = method_getImplementation(method)
        let function = unsafeBitCast(implementation, to: Function.self)

        return function(object, selector, argument)
    }
}
'''

FINAL_TRUE_TONE_UI = r'''
        // MARK: - True Tone Toggle
        VStack(alignment: .leading, spacing: spaceBeforeSubtitle) {
            HStack(alignment: .center, spacing: iconColumnWidth) {
                Image(systemName: "circle.lefthalf.filled")
                    .foregroundStyle(
                        trueToneController.isEnabled && trueToneController.isAvailable
                            ? .primary
                            : .secondary
                    )
                    .font(.system(size: 14))
                    .frame(width: 14, alignment: .leading)

                Text("True Tone")
                    .font(.system(size: 12, weight: .medium))
                    .frame(width: minSettingColumnWidth, alignment: .leading)

                Spacer()

                Toggle(
                    "",
                    isOn: Binding(
                        get: { trueToneController.isEnabled },
                        set: { newValue in
                            _ = trueToneController.setEnabled(newValue)
                        }
                    )
                )
                .labelsHidden()
                .toggleStyle(.switch)
                .controlSize(.small)
                .disabled(!trueToneController.isAvailable)
                .offset(x: 12)
            }

            HStack(spacing: iconColumnWidth) {
                Spacer()
                    .frame(width: 14)

                Text(
                    trueToneController.isAvailable
                        ? "Pas de kleurtemperatuur automatisch aan het omgevingslicht aan."
                        : "True Tone is momenteel niet beschikbaar."
                )
                .font(.system(size: 10))
                .foregroundStyle(.secondary)
                .opacity(0.8)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(.leading, settingPadding)
        .onReceive(
            Timer.publish(every: 0.5, on: .main, in: .common).autoconnect()
        ) { _ in
            trueToneController.refresh()
        }

'''

def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def find_function_span(text: str, name: str, include_docs: bool = False) -> tuple[int, int]:
    # Supports private/public/internal funcs, attributes are intentionally left in place.
    m = re.search(
        rf"(?m)^[ \t]*(?:private\s+|public\s+|internal\s+|fileprivate\s+)?func\s+{re.escape(name)}\s*\(",
        text,
    )
    if not m:
        fail(f"functie {name}() niet gevonden")

    start = m.start()
    if include_docs:
        while start > 0:
            prev_end = start - 1
            prev_start = text.rfind("\n", 0, prev_end) + 1
            line = text[prev_start:prev_end + 1]
            if re.match(r"^[ \t]*///", line) or not line.strip():
                start = prev_start
                continue
            break

    brace = text.find("{", m.start())
    if brace < 0:
        fail(f"openingsaccolade van {name}() niet gevonden")

    depth = 0
    i = brace
    in_string = False
    in_multiline = False
    escaped = False
    line_comment = False
    block_comment = 0

    while i < len(text):
        if not line_comment and block_comment == 0 and not in_string and text.startswith('"""', i):
            in_multiline = not in_multiline
            i += 3
            continue

        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_multiline:
            i += 1
            continue
        if line_comment:
            if ch == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "/" and nxt == "*":
                block_comment += 1
                i += 2
                continue
            if ch == "*" and nxt == "/":
                block_comment -= 1
                i += 2
                continue
            i += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = 1
            i += 2
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1

    fail(f"sluitaccolade van {name}() niet gevonden")
    raise AssertionError


def replace_function(text: str, old_names: tuple[str, ...], replacement: str) -> str:
    for name in old_names:
        try:
            start, end = find_function_span(text, name, include_docs=True)
            return text[:start] + replacement + text[end:]
        except SystemExit:
            pass
    fail(f"geen van deze functies gevonden: {', '.join(old_names)}")
    raise AssertionError


def replace_static_callback(text: str) -> str:
    marker = "private static let eventTapCallback: CGEventTapCallBack"
    start = text.find(marker)
    if start < 0:
        fail("eventTapCallback niet gevonden")

    # Include indentation and any immediately preceding /// doc line.
    start = text.rfind("\n", 0, start) + 1
    prev_end = start - 1
    if prev_end > 0:
        prev_start = text.rfind("\n", 0, prev_end) + 1
        if text[prev_start:prev_end + 1].lstrip().startswith("///"):
            start = prev_start

    eq = text.find("=", start)
    brace = text.find("{", eq)
    if brace < 0:
        fail("eventTapCallback openingsaccolade niet gevonden")

    depth = 0
    i = brace
    in_string = False
    escaped = False
    while i < len(text):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    # callback closure ends with "}"
                    end = i + 1
                    # consume optional trailing semicolon (normally absent) and newline
                    if end < len(text) and text[end] == ";":
                        end += 1
                    return text[:start] + FINAL_EVENT_CALLBACK + text[end:]
        i += 1

    fail("einde eventTapCallback niet gevonden")
    raise AssertionError


def insert_after_function(text: str, name: str, snippet: str) -> str:
    start, end = find_function_span(text, name)
    return text[:end] + snippet + text[end:]


def backup_originals() -> None:
    BACKUP_DIR.mkdir(exist_ok=True)
    for path in (BRIGHTNESS, MEDIA, HUD, APP, ABOUT):
        target = BACKUP_DIR / path.name
        if not target.exists():
            shutil.copy2(path, target)


def validate_source() -> None:
    if not SRC.is_dir():
        fail(f"{SRC} bestaat niet; voer dit uit vanuit de originele volumeHUD-3.3.3 hoofdmap")
    for path in (BRIGHTNESS, MEDIA, HUD, APP, ABOUT):
        if not path.is_file():
            fail(f"verwacht bronbestand ontbreekt: {path}")

    media = MEDIA.read_text(encoding="utf-8")
    brightness = BRIGHTNESS.read_text(encoding="utf-8")

    about = ABOUT.read_text(encoding="utf-8")
    core_already = "cgAnnotatedSessionEventTap" in media and "lastAnnotatedMediaKeyCode" in media
    true_tone_already = TRUE_TONE.exists() or "// MARK: - True Tone Toggle" in about

    if core_already or true_tone_already:
        if (
            core_already
            and TRUE_TONE.is_file()
            and "// MARK: - True Tone Toggle" in about
            and "setupMenuBarItem()" in APP.read_text(encoding="utf-8")
        ):
            print("Deze bron lijkt al met de volledige definitieve patch te zijn aangepast.")
            print("Er is niets gewijzigd.")
            raise SystemExit(0)
        fail(
            "de bron is al gedeeltelijk aangepast; gebruik deze definitieve patch "
            "op een schone originele volumeHUD v3.3.3-bronmap"
        )

    # Deliberately require the pristine v3.3.x baseline, not an intermediate patch state.
    if "private func getBuiltinDisplayID()" not in media:
        fail("MediaKeyInterceptor.swift lijkt niet op de originele v3.3.3-bron (getBuiltinDisplayID ontbreekt)")
    if "private func getBuiltinDisplayID()" not in brightness:
        fail("BrightnessMonitor.swift lijkt niet op de originele v3.3.3-bron (getBuiltinDisplayID ontbreekt)")

    app = APP.read_text(encoding="utf-8")
    required_app_markers = (
        "var aboutWindow: NSPanel?",
        "NSApplication.shared.setActivationPolicy(.accessory)",
        "// MARK: - Show About Window",
        "private func showAboutWindow()",
    )
    for marker in required_app_markers:
        if marker not in app:
            fail(f"VolumeHUDApp.swift lijkt niet op de verwachte v3.3.3-bron (ontbreekt: {marker})")

    required_about_markers = (
        '@AppStorage("brightnessEnabled") private var brightnessEnabled: Bool = false',
        '.animation(.easeInOut(duration: 0.3), value: brightnessEnabled)',
        '#endif // !SANDBOX',
        'spaceBeforeSubtitle',
        'iconColumnWidth',
        'minSettingColumnWidth',
        'settingPadding',
        '.onAppear',
    )
    for marker in required_about_markers:
        if marker not in about:
            fail(f"AboutView.swift lijkt niet op de verwachte v3.3.3-bron (ontbreekt: {marker})")

    if TRUE_TONE.exists():
        fail("TrueToneController.swift bestaat al; verwacht een schone originele v3.3.3-bronmap")


def patch_brightness_monitor() -> None:
    text = BRIGHTNESS.read_text(encoding="utf-8")

    text = replace_function(text, ("getBuiltinDisplayID",), FINAL_BRIGHTNESS_SELECTOR)
    text = replace_function(text, ("getCurrentBrightness",), FINAL_MONITOR_GET_CURRENT)

    BRIGHTNESS.write_text(text, encoding="utf-8")
    print("OK: BrightnessMonitor.swift")


def patch_hud_controller() -> None:
    text = HUD.read_text(encoding="utf-8")

    replacements = [
        (
            "Brightness HUD always shows on built-in display (since that's what it controls).",
            "Brightness HUD follows the preferred brightness display.",
        ),
        ("if let builtin = getBuiltinScreen() {", "if let brightnessScreen = getPreferredBrightnessScreen() {"),
        ("targetScreen = builtin", "targetScreen = brightnessScreen"),
        ('selectionReason = "brightness builtin"', 'selectionReason = "brightness preferred display"'),
        (
            'selectionReason = "brightness builtin-missing fallback NSScreen.main"',
            'selectionReason = "brightness preferred-display-missing fallback NSScreen.main"',
        ),
        (
            'selectionReason = "brightness builtin-missing fallback firstScreen"',
            'selectionReason = "brightness preferred-display-missing fallback firstScreen"',
        ),
    ]

    for old, new in replacements:
        if old not in text:
            fail(f"HUDController.swift baseline-fragment niet gevonden: {old}")
        text = text.replace(old, new, 1)

    # Make HUD Follows Mouse apply to Brightness HUD too.
    brightness_start = """            if hudType == .brightness {
                if let brightnessScreen = getPreferredBrightnessScreen() {"""
    brightness_new = """            let followMouse = UserDefaults.standard.bool(forKey: "volumeHUDFollowsMouse")

            if hudType == .brightness {
                if followMouse, let mouse = getScreenWithMouse() {
                    targetScreen = mouse
                    selectionReason = "brightness followsMouse"
                } else if let brightnessScreen = getPreferredBrightnessScreen() {"""
    if brightness_start not in text:
        fail("HUDController.swift brightness-selectieblok niet gevonden voor HUD Follows Mouse")
    text = text.replace(brightness_start, brightness_new, 1)

    duplicate_pref = """                // Check user preference for volume HUD location
                let followMouse = UserDefaults.standard.bool(forKey: "volumeHUDFollowsMouse")
                if followMouse {"""
    replacement_pref = """                // Check user preference for HUD location
                if followMouse {"""
    if duplicate_pref not in text:
        fail("HUDController.swift volume follow-mouse-fragment niet gevonden")
    text = text.replace(duplicate_pref, replacement_pref, 1)

    if "private func getPreferredBrightnessScreen() -> NSScreen?" not in text:
        text = insert_after_function(text, "getBuiltinScreen", FINAL_HUD_HELPER)

    HUD.write_text(text, encoding="utf-8")
    print("OK: HUDController.swift")


def patch_media_key_interceptor() -> None:
    text = MEDIA.read_text(encoding="utf-8")

    # Brightness display selection and setter path.
    text = replace_function(text, ("getBuiltinDisplayID",), FINAL_BRIGHTNESS_SELECTOR)
    text = replace_function(text, ("setBrightness",), FINAL_SET_BRIGHTNESS)
    text = replace_function(text, ("adjustBrightness",), FINAL_ADJUST_BRIGHTNESS)

    # Replace the original HID callback so tap disable/re-enable handles both taps.
    text = replace_static_callback(text)

    # Add annotated-session callback immediately before hudController.
    anchor = "    weak var hudController: HUDController?"
    if anchor not in text:
        fail("hudController-invoegpunt niet gevonden")
    text = text.replace(anchor, FINAL_SESSION_CALLBACK + "\n" + anchor, 1)

    # Add second tap state and 50ms dedup state.
    prop_anchor = """    private var eventTap: CFMachPort?
    private var runLoopSource: CFRunLoopSource?
"""
    prop_replacement = """    private var eventTap: CFMachPort?
    private var runLoopSource: CFRunLoopSource?

    // Annotated-session tap for synthetic media events (for example Stream Deck).
    private var sessionEventTap: CFMachPort?
    private var sessionRunLoopSource: CFRunLoopSource?

    // Stream Deck can emit the same synthetic media-key down event twice.
    private nonisolated(unsafe) var lastAnnotatedMediaKeyCode: Int?
    private nonisolated(unsafe) var lastAnnotatedMediaKeyTime: TimeInterval = 0
    private let annotatedMediaKeyDeduplicationWindow: TimeInterval = 0.05
"""
    if prop_anchor not in text:
        fail("eventTap/runLoopSource-properties niet gevonden")
    text = text.replace(prop_anchor, prop_replacement, 1)

    # Replace lifecycle functions as a unit, avoiding fragile line-based inserts.
    text = replace_function(text, ("start",), FINAL_START)
    text = replace_function(text, ("stop",), FINAL_STOP)

    MEDIA.write_text(text, encoding="utf-8")
    print("OK: MediaKeyInterceptor.swift")


def patch_volumehud_app() -> None:
    text = APP.read_text(encoding="utf-8")

    if "menuBarItemClicked" in text or "setupMenuBarItem()" in text:
        print("OK: VolumeHUDApp.swift (menubalkfunctie bestond al)")
        return

    text = text.replace(
        "    var aboutWindow: NSPanel?\n",
        "    var aboutWindow: NSPanel?\n"
        "    private var statusItem: NSStatusItem?\n",
        1,
    )

    text = text.replace(
        "        NSApplication.shared.setActivationPolicy(.accessory)\n",
        "        NSApplication.shared.setActivationPolicy(.accessory)\n"
        "        setupMenuBarItem()\n",
        1,
    )

    menu_code = r'''
    // MARK: - Menu Bar

    /// Add a persistent volumeHUD icon to the macOS menu bar.
    /// A normal left-click opens the existing About/settings window.
    private func setupMenuBarItem() {
        guard statusItem == nil else { return }

        let item = NSStatusBar.system.statusItem(withLength: 48)

        if let button = item.button {
            if let iconURL = Bundle.main.url(forResource: "MenuBarIcon", withExtension: "svg"),
               let image = NSImage(contentsOf: iconURL) {
                image.isTemplate = true
                image.size = NSSize(width: 44, height: 22)
                button.image = image
                button.imageScaling = .scaleProportionallyDown
            } else {
                let image = NSImage(
                    systemSymbolName: "speaker.wave.2.fill",
                    accessibilityDescription: "volumeHUD"
                )
                image?.isTemplate = true
                button.image = image
            }

            button.toolTip = "volumeHUD"
            button.target = self
            button.action = #selector(menuBarItemClicked(_:))
            button.sendAction(on: [.leftMouseUp])
        }

        statusItem = item
    }

    @objc
    private func menuBarItemClicked(_: Any?) {
        showAboutWindow()
    }

'''

    marker = "    // MARK: - Show About Window\n"
    if marker not in text:
        fail("VolumeHUDApp.swift: About-invoegpunt niet gevonden")
    text = text.replace(marker, menu_code + marker, 1)

    required = (
        "private var statusItem: NSStatusItem?",
        "setupMenuBarItem()",
        'forResource: "MenuBarIcon"',
        "#selector(menuBarItemClicked(_:))",
        "showAboutWindow()",
    )
    for item in required:
        if item not in text:
            fail(f"VolumeHUDApp.swift menubalkpatch incompleet: {item}")

    APP.write_text(text, encoding="utf-8")
    RESOURCES.mkdir(parents=True, exist_ok=True)
    MENU_ICON.write_text(FINAL_MENU_ICON_SVG, encoding="utf-8")
    print("OK: VolumeHUDApp.swift")
    print("OK: Resources/MenuBarIcon.svg")



def patch_true_tone() -> None:
    text = ABOUT.read_text(encoding="utf-8")

    if "import Combine" not in text:
        if "import SwiftUI\n" in text:
            text = text.replace("import SwiftUI\n", "import Combine\nimport SwiftUI\n", 1)
        else:
            text = "import Combine\n" + text

    brightness_property = '@AppStorage("brightnessEnabled") private var brightnessEnabled: Bool = false'
    state_line = '    @StateObject private var trueToneController = TrueToneController()\n'
    if "trueToneController = TrueToneController()" not in text:
        text = text.replace(
            brightness_property + "\n",
            brightness_property + "\n" + state_line,
            1,
        )

    brightness_animation = '.animation(.easeInOut(duration: 0.3), value: brightnessEnabled)'
    animation_pos = text.find(brightness_animation)
    if animation_pos < 0:
        fail("AboutView.swift: brightness-sectie niet gevonden")

    endif_marker = '#endif // !SANDBOX'
    endif_pos = text.find(endif_marker, animation_pos)
    if endif_pos < 0:
        fail("AboutView.swift: einde van niet-sandbox instellingen niet gevonden")

    text = text[:endif_pos] + FINAL_TRUE_TONE_UI + "        " + text[endif_pos:]

    text, frame_count = re.subn(
        r'\.frame\(width:\s*540,\s*height:\s*\d+\)',
        '.frame(width: 540, height: 350)',
        text,
        count=1,
    )
    if frame_count != 1:
        fail("AboutView.swift: About-vensterformaat niet eenduidig gevonden")

    # Refresh once when the About window appears; the timer below keeps it live.
    if ".onAppear" not in text:
        fail("AboutView.swift: onAppear ontbreekt")
    text, appear_count = re.subn(
        r'(\.onAppear\s*\{\s*\n)',
        r'\1            trueToneController.refresh()\n',
        text,
        count=1,
    )
    if appear_count != 1:
        fail("AboutView.swift: onAppear niet eenduidig gevonden")

    ABOUT.write_text(text, encoding="utf-8")
    TRUE_TONE.write_text(FINAL_TRUE_TONE_CONTROLLER, encoding="utf-8")
    print("OK: AboutView.swift")
    print("OK: TrueToneController.swift")

def validate_result() -> None:
    media = MEDIA.read_text(encoding="utf-8")
    brightness = BRIGHTNESS.read_text(encoding="utf-8")
    hud = HUD.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    about = ABOUT.read_text(encoding="utf-8")
    true_tone = TRUE_TONE.read_text(encoding="utf-8") if TRUE_TONE.is_file() else ""

    checks = {
        "Studio Display selector": "CGDisplayVendorNumber($0) == 0x0610" in media
            and "CGDisplayVendorNumber($0) == 0x0610" in brightness,
        "DisplayServices setter notification": 'dlsym(handle, "DisplayServicesBrightnessChanged")' in media,
        "Annotated session tap": "tap: .cgAnnotatedSessionEventTap" in media,
        "Stream Deck dedup": "lastAnnotatedMediaKeyCode" in media
            and "annotatedMediaKeyDeduplicationWindow" in media,
        "Synthetic volume/mute support": "Annotated-session media event detected" in media,
        "Brightness HUD target": "getPreferredBrightnessScreen()" in hud,
        "Brightness HUD follows mouse": 'selectionReason = "brightness followsMouse"' in hud
            and 'UserDefaults.standard.bool(forKey: "volumeHUDFollowsMouse")' in hud,
        "Menu bar opens About": "private var statusItem: NSStatusItem?" in app
            and "#selector(menuBarItemClicked(_:))" in app
            and "showAboutWindow()" in app,
        "Custom menu bar icon": 'forResource: "MenuBarIcon"' in app
            and "withLength: 48" in app
            and MENU_ICON.is_file()
            and 'opacity=".32"' in MENU_ICON.read_text(encoding="utf-8"),
        "True Tone controller": "CBTrueToneClient" in true_tone
            and 'selectorName: "setEnabled:"' in true_tone,
        "True Tone About UI": "// MARK: - True Tone Toggle" in about
            and 'Text("True Tone")' in about
            and "Timer.publish(every: 0.5" in about
            and ".offset(x: 12)" in about
            and "trueToneController.refresh()" in about,
        "No automatic-brightness experiment": "AutoBrightnessController" not in about
            and not (SRC / "AutoBrightnessController.swift").exists(),
    }

    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        fail("eindcontrole mislukt: " + ", ".join(failed))

    print()
    print("Eindcontrole:")
    for name in checks:
        print(f"  OK: {name}")


def main() -> None:
    print("volumeHUD 3.3.3 - totaalpatch: Studio Display + Stream Deck + menubalkicoon + True Tone")
    print(f"Bronmap: {ROOT}")
    print()

    validate_source()
    backup_originals()
    patch_brightness_monitor()
    patch_hud_controller()
    patch_media_key_interceptor()
    patch_volumehud_app()
    patch_true_tone()
    validate_result()

    print()
    print("KLAAR.")
    print(f"Originele vijf Swift-bestanden staan in: {BACKUP_DIR}")
    print()
    print("Bouw daarna met:")
    print("  ./build_volumehud_cli_v4.sh")
    print()
    print("Na de eerste start moeten Toegankelijkheid en Invoermonitoring")
    print("voor de custom volumeHUD.app toegestaan zijn.")


if __name__ == "__main__":
    main()
