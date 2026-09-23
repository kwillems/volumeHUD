//
//  NightShiftController.swift
//  volumeHUD
//
//  Controls macOS Night Shift through Apple's private CoreBrightness framework.
//

import Combine
import Darwin
import Foundation
import ObjectiveC

@MainActor
final class NightShiftController: ObservableObject {
    @Published private(set) var isEnabled = false
    @Published private(set) var isAvailable = false

    private var frameworkHandle: UnsafeMutableRawPointer?
    private var client: NSObject?

    // Layout used by CBBlueLightClient getBlueLightStatus:
    private struct BlueLightStatus {
        var active: UInt8 = 0
        var enabled: UInt8 = 0
        var sunSchedulePermitted: UInt8 = 0
        var padding: UInt8 = 0

        var mode: Int32 = 0

        var fromHour: Int32 = 0
        var fromMinute: Int32 = 0
        var toHour: Int32 = 0
        var toMinute: Int32 = 0

        var disableFlags: UInt64 = 0
    }

    init() {
        loadClient()
        refresh()
    }

    private func loadClient() {
        let frameworkPath =
            "/System/Library/PrivateFrameworks/CoreBrightness.framework/CoreBrightness"

        frameworkHandle = dlopen(frameworkPath, RTLD_NOW | RTLD_LOCAL)

        guard frameworkHandle != nil else {
            isAvailable = false
            return
        }

        guard let clientType =
            NSClassFromString("CBBlueLightClient") as? NSObject.Type
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

        var status = BlueLightStatus()

        let success = getStatus(
            client,
            status: &status
        )

        isAvailable = success
        isEnabled = success && status.enabled != 0
    }

    @discardableResult
    func setEnabled(_ enabled: Bool) -> Bool {
        guard isAvailable, let client else {
            return false
        }

        let selector = NSSelectorFromString("setEnabled:")

        guard let method = class_getInstanceMethod(
            type(of: client),
            selector
        ) else {
            return false
        }

        typealias Function = @convention(c) (
            AnyObject,
            Selector,
            Bool
        ) -> Bool

        let implementation = method_getImplementation(method)

        let function = unsafeBitCast(
            implementation,
            to: Function.self
        )

        let success = function(
            client,
            selector,
            enabled
        )

        refresh()
        return success
    }

    private func getStatus(
        _ object: NSObject,
        status: inout BlueLightStatus
    ) -> Bool {
        let selector = NSSelectorFromString("getBlueLightStatus:")

        guard let method = class_getInstanceMethod(
            type(of: object),
            selector
        ) else {
            return false
        }

        typealias Function = @convention(c) (
            AnyObject,
            Selector,
            UnsafeMutableRawPointer
        ) -> Bool

        let implementation = method_getImplementation(method)

        let function = unsafeBitCast(
            implementation,
            to: Function.self
        )

        return withUnsafeMutablePointer(to: &status) { pointer in
            function(
                object,
                selector,
                UnsafeMutableRawPointer(pointer)
            )
        }
    }
}
