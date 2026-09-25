//

//  AboutView.swift

//  by Danny Stewart (2025)

//  MIT License

//  https://github.com/dannystewart/volumeHUD

//

import AppKit

import Combine

import SwiftUI

// MARK: - AboutView

struct AboutView: View {

// Settings for app preferences

    #if !SANDBOX

        @AppStorage("brightnessEnabled") private var brightnessEnabled: Bool = false

    @StateObject private var trueToneController = TrueToneController()

    @StateObject private var nightShiftController = NightShiftController()

    #endif // !SANDBOX

    @AppStorage("volumeHUDFollowsMouse") private var volumeHUDFollowsMouse: Bool = true

    @AppStorage("useRelativePositioning") private var useRelativePositioning: Bool = true

    @AppStorage("appAppearance") private var appAppearance: String = "system"
    #if !SANDBOX

    private enum UpdateStatus {
        case checking
        case upToDate
        case available(version: String, url: URL)
        case failed
    }

    @State private var updateStatus: UpdateStatus = .checking

    // GitHub repository used for update checks
    private let githubOwner = "kwillems"
    private let githubRepo = "volumeHUD"

    #endif // !SANDBOX

/// Login item manager

    @Environment(\.loginItemManager) private var loginItemManager

    let onQuit: () -> Void

    weak var appDelegate: AppDelegate?

    let logger: Logger = .init()

// Visual alignment

    private let iconColumnWidth: CGFloat = 20

    private let minSettingColumnWidth: CGFloat = 140

    private let settingPadding: CGFloat = 24 // Higher for less padding

    private let spaceBeforeSubtitle: CGFloat = -3

/// App version, e.g. 3.3.3

    private var appVersion: String {

        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "3.3.3"

    }

/// Build number, e.g. 2

    private var buildNumber: String {

        Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "0"

    }

/// User-facing version, e.g. 3.3.3+2

    private var displayVersion: String {

        "\(appVersion)+\(buildNumber)"

    }

/// GitHub release for this custom build

    private var releaseURL: URL {

        URL(

            string: "https://github.com/kwillems/volumeHUD/releases/tag/v\(appVersion)-custom.\(buildNumber)"

        )!

    }

// MARK: - About View

    var body: some View {

        HStack(alignment: .top, spacing: 20) {

// MARK: - Left Column (App Info and Quit Button)

            VStack(spacing: 8) {

                if let appIcon = NSImage(named: "volumeHUD") {

                    Image(nsImage: appIcon)

                        .resizable()

                        .frame(width: 80, height: 80)

                }

                Text("volumeHUD")

                    .font(.system(size: 24, weight: .medium))

                VStack(spacing: 3) {

                    Link(

                        "Version \(displayVersion)",

                        destination: releaseURL

                    )

                    .font(.system(size: 11))

                    .foregroundStyle(.blue)

                    .underline()

                    Text("by Koen Willems")

                        .font(.system(size: 12))

                        .foregroundStyle(.secondary)

                #if !SANDBOX
                    updateStatusView
                #endif

                }

                VStack(spacing: 3) {

                    HStack(spacing: 0) {

                        Text("Based on ")

                            .foregroundStyle(.secondary)

                        Link(

                            "volumeHUD 3.3.3",

                            destination: URL(

                                string: "https://github.com/dannystewart/volumeHUD/releases/tag/v3.3.3"

                            )!

                        )

                        .foregroundStyle(.blue)

                        .underline()

                    }

                    Text("Original project by Danny Stewart")

                        .foregroundStyle(.secondary)

                }

                .font(.system(size: 11))

                .padding(.top, 8)

                Spacer(minLength: 0)

                Button(action: onQuit) {

                    Text("Quit volumeHUD")

                        .frame(maxWidth: .infinity)

                }

                .buttonStyle(.borderedProminent)

                .controlSize(.large)

                .keyboardShortcut(.defaultAction)

            }

            .frame(width: 160, alignment: .top)

            .padding(.leading, 16)

// MARK: - Right Column (Settings)

            VStack(alignment: .leading, spacing: 15) {

// MARK: - Open at Login Setting

                if let loginItemManager {

                    LoginItemSetting(

                        loginItemManager: loginItemManager,

                        iconColumnWidth: iconColumnWidth,

                        minSettingColumnWidth: minSettingColumnWidth,

                        settingPadding: settingPadding,

                        spaceBeforeSubtitle: spaceBeforeSubtitle,

                    )

                }

                #if !SANDBOX

// MARK: - Brightness HUD Toggle

                    VStack(alignment: .leading, spacing: spaceBeforeSubtitle) {

                        HStack(alignment: .center, spacing: iconColumnWidth) {

                            Image(systemName: "sun.max.fill")

                                .foregroundStyle(brightnessEnabled ? .orange : .gray)

                                .font(.system(size: 14))

                                .frame(width: 14, alignment: .leading)

                                .animation(.easeInOut(duration: 0.3), value: brightnessEnabled)

                            Text("Brightness HUD")

                                .font(.system(size: 12, weight: .medium))

                                .frame(width: minSettingColumnWidth, alignment: .leading)

                            Spacer()

                            Toggle("", isOn: $brightnessEnabled)

                                .toggleStyle(SwitchToggleStyle(tint: .accentColor))

                                .scaleEffect(0.8)

                                .onChange(of: brightnessEnabled) { oldValue, newValue in

                                    logger.debug("Brightness setting changed from \(oldValue) to \(newValue).")

                                    appDelegate?.startBrightnessMonitoringIfEnabled()

                                }

                        }

                    }

                    .padding(.leading, settingPadding)

                    .animation(.easeInOut(duration: 0.3), value: brightnessEnabled)

                #endif // !SANDBOX

// MARK: - Display Toggle for HUD Placement

                VStack(alignment: .leading, spacing: spaceBeforeSubtitle) {

                    HStack(alignment: .center, spacing: iconColumnWidth) {

                        Image(systemName: volumeHUDFollowsMouse ? "cursorarrow.click.2" : "laptopcomputer")

                            .foregroundStyle(volumeHUDFollowsMouse ? .blue : .gray)

                            .font(.system(size: 14))

                            .frame(width: 14, alignment: .leading)

                            .animation(.easeInOut(duration: 0.3), value: volumeHUDFollowsMouse)

                        Text("HUD Follows Mouse")

                            .font(.system(size: 12, weight: .medium))

                            .frame(width: minSettingColumnWidth, alignment: .leading)

                        Spacer()

                        Toggle("", isOn: $volumeHUDFollowsMouse)

                            .toggleStyle(SwitchToggleStyle(tint: .accentColor))

                            .scaleEffect(0.8)

                            .onChange(of: volumeHUDFollowsMouse) { oldValue, newValue in

                                logger.debug("Volume HUD display setting changed from \(oldValue) to \(newValue).")

                            }

                    }

                    HStack(spacing: iconColumnWidth) {

                        Spacer()

                            .frame(width: 14)

                        Text(volumeHUDFollowsMouse ? "Show on screen with mouse cursor" : "Always show on the primary display")

                            .font(.system(size: 10))

                            .foregroundStyle(.secondary)

                            .opacity(0.8)

                            .frame(maxWidth: .infinity, alignment: .leading)

                    }

                }

                .padding(.leading, settingPadding)

                .animation(.easeInOut(duration: 0.3), value: volumeHUDFollowsMouse)

// MARK: - Relative Positioning Toggle

                VStack(alignment: .leading, spacing: spaceBeforeSubtitle) {

                    HStack(alignment: .center, spacing: iconColumnWidth) {

                        Image(systemName: useRelativePositioning ? "arrow.up.and.down.text.horizontal" : "arrow.down.to.line")

                            .foregroundStyle(useRelativePositioning ? .cyan : .gray)

                            .font(.system(size: 14))

                            .frame(width: 14, alignment: .leading)

                            .animation(.easeInOut(duration: 0.3), value: useRelativePositioning)

                        Text("Relative HUD Position")

                            .font(.system(size: 12, weight: .medium))

                            .frame(width: minSettingColumnWidth, alignment: .leading)

                        Spacer()

                        Toggle("", isOn: $useRelativePositioning)

                            .toggleStyle(SwitchToggleStyle(tint: .accentColor))

                            .scaleEffect(0.8)

                            .onChange(of: useRelativePositioning) { oldValue, newValue in

                                logger.debug("Relative positioning setting changed from \(oldValue) to \(newValue).")

                            }

                    }

                    HStack(spacing: iconColumnWidth) {

                        Spacer()

                            .frame(width: 14)

                        Text(useRelativePositioning ? "Relative percentage from bottom" : "Absolute from bottom (Apple default)")

                            .font(.system(size: 10))

                            .foregroundStyle(.secondary)

                            .opacity(0.8)

                            .frame(maxWidth: .infinity, alignment: .leading)

                    }

                }

                .padding(.leading, settingPadding)

                .animation(.easeInOut(duration: 0.3), value: useRelativePositioning)

                #if !SANDBOX

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

                                    ? "Automatically adjust the color temperature to ambient light."

                                    : "True Tone is currently unavailable."

                            )

                            .font(.system(size: 10))

                            .foregroundStyle(.secondary)

                            .opacity(0.8)

                            .frame(maxWidth: .infinity, alignment: .leading)

                        }

                    }

                    .padding(.leading, settingPadding)

                    

// MARK: - Night Shift Toggle

                    VStack(alignment: .leading, spacing: spaceBeforeSubtitle) {

                        HStack(alignment: .center, spacing: iconColumnWidth) {

                            Image(systemName: "moon.fill")

                                .foregroundStyle(

                                    nightShiftController.isEnabled && nightShiftController.isAvailable

                                        ? .orange

                                        : .gray

                                )

                                .font(.system(size: 14))

                                .frame(width: 14, alignment: .leading)

                                .animation(

                                    .easeInOut(duration: 0.3),

                                    value: nightShiftController.isEnabled

                                )

                            Text("Night Shift")

                                .font(.system(size: 12, weight: .medium))

                                .frame(width: minSettingColumnWidth, alignment: .leading)

                            Spacer()

                            Toggle(

                                "",

                                isOn: Binding(

                                    get: { nightShiftController.isEnabled },

                                    set: { nightShiftController.setEnabled($0) }

                                )

                            )

                            .toggleStyle(SwitchToggleStyle(tint: .accentColor))

                            .scaleEffect(0.8)

                            .disabled(!nightShiftController.isAvailable)

                        }

                        HStack(spacing: iconColumnWidth) {

                            Spacer()

                                .frame(width: 14)

                            Text(

                                nightShiftController.isAvailable

                                    ? "Reduce blue light with a warmer display."

                                    : "Night Shift is unavailable."

                            )

                            .font(.system(size: 10))

                            .foregroundStyle(.secondary)

                            .opacity(0.8)

                            .frame(maxWidth: .infinity, alignment: .leading)

                        }

                    }

                    .padding(.leading, settingPadding)

                #endif // !SANDBOX

// MARK: - Appearance

                VStack(alignment: .leading, spacing: 6) {

                    HStack(alignment: .center, spacing: iconColumnWidth) {

                        Image(systemName: "circle.righthalf.filled")

                            .foregroundStyle(.secondary)

                            .font(.system(size: 14))

                            .frame(width: 14, alignment: .leading)

                        Text("Appearance")

                            .font(.system(size: 12, weight: .medium))

                            .frame(width: minSettingColumnWidth, alignment: .leading)

                        Spacer()

                    }

                    Picker("", selection: $appAppearance) {

                        Text("System").tag("system")

                        Text("Light").tag("light")

                        Text("Dark").tag("dark")

                    }

                    .labelsHidden()

                    .pickerStyle(.segmented)

                    .frame(width: 220)

                    .padding(.leading, 34)

                    .onChange(of: appAppearance) { _, newValue in

                        applyAppearance(newValue)

                    }

                }

                .padding(.leading, settingPadding)

                Spacer(minLength: 0)

            }

            .padding(.trailing, 6) // Right side window padding

        }

        .padding(32) // Overall frame padding

        .frame(width: 540, height: 450)

        .onAppear {

            applyAppearance(appAppearance)

        }

        #if !SANDBOX

            .onAppear {

            trueToneController.refresh()
                nightShiftController.refresh()

                Task {

                    try? await Task.sleep(nanoseconds: 200_000_000) // 0.2 second delay

                    checkForUpdates()

                }

            }

        #endif // !SANDBOX

    }

// MARK: - Appearance

    private func applyAppearance(_ value: String) {

        switch value {

        case "light":

            NSApp.appearance = NSAppearance(named: .aqua)

        case "dark":

            NSApp.appearance = NSAppearance(named: .darkAqua)

        default:

            NSApp.appearance = nil

        }

    }
    #if !SANDBOX

    @ViewBuilder
    private var updateStatusView: some View {
        switch updateStatus {
        case .checking:
            HStack(spacing: 4) {
                ProgressView()
                    .controlSize(.small)

                Text("Checking for updates…")
            }
            .font(.system(size: 10))
            .foregroundStyle(.secondary)
            .padding(.top, 2)

        case .upToDate:
            Label("Up to date", systemImage: "checkmark.circle.fill")
                .font(.system(size: 10))
                .foregroundStyle(.green)
                .padding(.top, 2)

        case let .available(version, url):
            Link(destination: url) {
                Label(
                    "Update available: \(version)",
                    systemImage: "arrow.down.circle.fill"
                )
            }
            .font(.system(size: 10))
            .foregroundStyle(.blue)
            .padding(.top, 2)

        case .failed:
            Text("Unable to check for updates")
                .font(.system(size: 10))
                .foregroundStyle(.secondary)
                .padding(.top, 2)
        }
    }

    // MARK: - Update Check

    private struct GitHubRelease {
        let tagName: String
        let url: URL
    }

    private struct ParsedVersion {
        let components: [Int]
        let build: Int

        var displayString: String {
            "\(components.map(String.init).joined(separator: "."))+\(build)"
        }
    }

    private func checkForUpdates() {
        Task {
            do {
                let release = try await fetchLatestRelease()

                guard
                    let latestVersion = parseVersion(release.tagName),
                    let currentVersion = parseVersion("\(appVersion)+\(buildNumber)")
                else {
                    throw URLError(.cannotParseResponse)
                }

                let updateAvailable = isNewerVersion(
                    latestVersion,
                    than: currentVersion
                )

                await MainActor.run {
                    if updateAvailable {
                        updateStatus = .available(
                            version: latestVersion.displayString,
                            url: release.url
                        )
                    } else {
                        updateStatus = .upToDate
                    }
                }
            } catch {
                logger.error("Update check failed: \(error)")

                await MainActor.run {
                    updateStatus = .failed
                }
            }
        }
    }

    private func fetchLatestRelease() async throws -> GitHubRelease {
        let urlString =
            "https://api.github.com/repos/\(githubOwner)/\(githubRepo)/releases/latest"

        guard let url = URL(string: urlString) else {
            throw URLError(.badURL)
        }

        var request = URLRequest(url: url)
        request.setValue(
            "application/vnd.github.v3+json",
            forHTTPHeaderField: "Accept"
        )

        let (data, response) = try await URLSession.shared.data(for: request)

        guard
            let httpResponse = response as? HTTPURLResponse,
            httpResponse.statusCode == 200
        else {
            throw URLError(.badServerResponse)
        }

        guard
            let json = try JSONSerialization.jsonObject(with: data)
                as? [String: Any],
            let tagName = json["tag_name"] as? String
        else {
            throw URLError(.cannotParseResponse)
        }

        let releaseURL: URL

        if
            let htmlURL = json["html_url"] as? String,
            let url = URL(string: htmlURL)
        {
            releaseURL = url
        } else {
            guard let url = URL(
                string:
                    "https://github.com/\(githubOwner)/\(githubRepo)/releases/latest"
            ) else {
                throw URLError(.badURL)
            }

            releaseURL = url
        }

        return GitHubRelease(
            tagName: tagName,
            url: releaseURL
        )
    }

    private func parseVersion(_ value: String) -> ParsedVersion? {
        var version = value.trimmingCharacters(
            in: .whitespacesAndNewlines
        )

        if version.hasPrefix("v") {
            version.removeFirst()
        }

        let baseVersion: String
        let buildString: String

        if let range = version.range(of: "-custom.") {
            baseVersion = String(version[..<range.lowerBound])
            buildString = String(version[range.upperBound...])
        } else if let plusIndex = version.lastIndex(of: "+") {
            baseVersion = String(version[..<plusIndex])
            buildString = String(version[version.index(after: plusIndex)...])
        } else {
            baseVersion = version
            buildString = "0"
        }

        let components = baseVersion
            .split(separator: ".")
            .compactMap { Int($0) }

        guard
            components.count == 3,
            let build = Int(buildString)
        else {
            return nil
        }

        return ParsedVersion(
            components: components,
            build: build
        )
    }

    private func isNewerVersion(
        _ latest: ParsedVersion,
        than current: ParsedVersion
    ) -> Bool {
        for index in 0 ..< max(
            latest.components.count,
            current.components.count
        ) {
            let latestPart =
                index < latest.components.count
                    ? latest.components[index]
                    : 0

            let currentPart =
                index < current.components.count
                    ? current.components[index]
                    : 0

            if latestPart > currentPart {
                return true
            }

            if latestPart < currentPart {
                return false
            }
        }

        return latest.build > current.build
    }

    private func openReleasesPage() {
        let urlString =
            "https://github.com/\(githubOwner)/\(githubRepo)/releases/latest"

        if let url = URL(string: urlString) {
            NSWorkspace.shared.open(url)
        }
    }

    #endif // !SANDBOX

}

// MARK: - LoginItemSetting

private struct LoginItemSetting: View {

    @ObservedObject private var loginItemManager: LoginItemManager

    let iconColumnWidth: CGFloat

    let minSettingColumnWidth: CGFloat

    let settingPadding: CGFloat

    let spaceBeforeSubtitle: CGFloat

    init(

loginItemManager: LoginItemManager,

iconColumnWidth: CGFloat,

minSettingColumnWidth: CGFloat,

settingPadding: CGFloat,

spaceBeforeSubtitle: CGFloat,

    ) {

        self.loginItemManager = loginItemManager

        self.iconColumnWidth = iconColumnWidth

        self.minSettingColumnWidth = minSettingColumnWidth

        self.settingPadding = settingPadding

        self.spaceBeforeSubtitle = spaceBeforeSubtitle

    }

    var body: some View {

        VStack(alignment: .leading, spacing: spaceBeforeSubtitle) {

            HStack(alignment: .center, spacing: iconColumnWidth) {

                Image(systemName: "power.circle.fill")

                    .foregroundStyle(loginItemManager.isEnabled ? .green : .gray)

                    .font(.system(size: 14))

                    .frame(width: 14, alignment: .leading)

                    .animation(.easeInOut(duration: 0.3), value: loginItemManager.isEnabled)

                Text("Open at Login")

                    .font(.system(size: 12, weight: .medium))

                    .frame(width: minSettingColumnWidth, alignment: .leading)

                Spacer()

                Toggle("", isOn: Binding(

                    get: { loginItemManager.isEnabled },

                    set: { loginItemManager.setEnabled($0) },

                ))

                .toggleStyle(SwitchToggleStyle(tint: .accentColor))

                .scaleEffect(0.8)

            }

        }

        .padding(.leading, settingPadding)

    }

}

#Preview {

    AboutView(

        onQuit: {},

        appDelegate: nil,

    )

    .environment(\.loginItemManager, LoginItemManager())

}
