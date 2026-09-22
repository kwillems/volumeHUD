//
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
