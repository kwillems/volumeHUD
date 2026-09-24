# volumeHUD — Studio Display custom fork

A customized fork of [dannystewart/volumeHUD](https://github.com/dannystewart/volumeHUD), created to bring back the familiar classic macOS HUD and make it work more naturally with my own setup:

- **MacBook Pro**
- **Apple Studio Display**
- **Stream Deck**
- **macOS Tahoe**

## Why this fork exists

With macOS Tahoe, Apple changed the traditional centered volume and brightness HUD into a much smaller indicator near the top-right of the screen.
I preferred the old HUD. It is larger, immediately visible and much easier to read at a glance.
That led me to [volumeHUD](https://github.com/dannystewart/volumeHUD), which restores the classic pre-Tahoe macOS HUD.
The original project already solved the main problem, but my setup introduced a few additional requirements. I use a MacBook Pro connected to an Apple Studio Display, with a Stream Deck for volume and brightness control. I wanted the restored HUD to behave naturally in that configuration as well.
This fork grew from that use case.

## Interface

The fork adds a settings/About window for the additional HUD and display features.

<table>
  <tr>
    <td align="center">
      <img src="images/settings_light.png" width="500"><br>
      <sub>Light appearance</sub>
    </td>
    <td align="center">
      <img src="images/settings_dark.png" width="500"><br>
      <sub>Dark appearance</sub>
    </td>
  </tr>
</table>

## Based on volumeHUD

The original volumeHUD restores the classic macOS HUD for media-key actions such as volume, mute and display brightness.
This fork keeps that core behaviour and adds several features aimed primarily at using a MacBook Pro together with an Apple Studio Display.

## Added in this fork

### Apple Studio Display brightness control

One of the main additions in this fork is direct brightness control for an attached **Apple Studio Display**.
The fork uses Apple's `DisplayServices` framework for brightness control, allowing brightness changes to be applied to the Studio Display while still using the restored classic HUD.
This was one of the main reasons for creating the fork.

### Brightness HUD

The restored classic HUD can also be used for brightness changes.
The **Brightness HUD** option can be enabled or disabled independently in the application window.

### Stream Deck support

The fork is designed to work with the standard Stream Deck media controls.
In my setup I use the built-in actions under:

**System → Multimedia**

including:

- Increase Screen Brightness
- Decrease Screen Brightness
- Volume Up
- Volume Down
- Mute

No custom Stream Deck plugin is required.
The Stream Deck generates the normal macOS media-key events and volumeHUD handles them, including routing brightness changes to the Studio Display.

### HUD Follows Mouse

When **HUD Follows Mouse** is enabled, brightness control and the brightness HUD follow the display containing the mouse pointer.
For example, with both the MacBook display and Studio Display active:

- move the pointer to the Studio Display and adjust brightness → the Studio Display is adjusted
- move the pointer to the MacBook display and adjust brightness → the MacBook display is adjusted

Volume and mute remain associated with the normal macOS audio output device.

### Relative HUD Position

The original classic HUD has a fixed visual style, but its exact vertical position may not be ideal on every display.
The **Relative HUD Position** option places the HUD using a relative percentage from the bottom of the screen.
This makes the HUD position scale more naturally between displays with different sizes and resolutions.

### True Tone

True Tone can be controlled directly from volumeHUD.
This makes it possible to enable or disable True Tone without opening System Settings.

### Night Shift

Night Shift control is also available from the volumeHUD window.
This provides quick access to the warmer display mode from the same place as the other display-related settings.

### Appearance

The application window can use:

- **System**
- **Light**
- **Dark**

The selected appearance applies to the volumeHUD interface independently of the current macOS appearance when desired.

### Open at Login

**Open at Login** can be enabled directly from the application.

This allows volumeHUD to start automatically after signing in to macOS.

### Custom menu bar icon

This fork uses a custom menu bar icon that combines the two main functions of the application:

- audio
- display control

The icon visually matches the role the application now has in this fork.

### Settings and About window

This fork adds a combined settings and About window containing:

- version information
- credit to the original volumeHUD project
- Open at Login
- Brightness HUD
- HUD Follows Mouse
- Relative HUD Position
- True Tone
- Night Shift
- appearance controls
- a Quit button

## Behaviour overview

| Action | Behaviour |
|---|---|
| Volume Up / Down | Controls the current macOS audio output |
| Mute | Controls the current macOS audio output |
| Brightness Up / Down | Controls display brightness |
| Brightness HUD | Shows the classic-style brightness HUD |
| HUD Follows Mouse | Shows the HUD on the display containing the pointer |
| Relative HUD Position | Positions the HUD using a relative percentage from the bottom |
| Stream Deck media controls | Uses the standard Stream Deck multimedia actions |
| True Tone | Can be toggled from volumeHUD |
| Night Shift | Can be toggled from volumeHUD |
| Appearance | System, Light or Dark |
| Open at Login | Starts volumeHUD automatically after login |

## My setup

This fork is primarily developed and tested with:

- a **MacBook Pro**
- an **Apple Studio Display**
- a **Stream Deck**
- **macOS Tahoe**

The additional functionality was created for this configuration first.
Other display setups may work as well, but they are not the primary focus of the fork.

## Building

The project can be built from the command line with:

```bash
tools/build_volumehud_cli.sh
```

The build script is located in the `tools` directory.
No Homebrew installation is required for this build method.

## Project structure

Some of the areas changed or added in this fork include the code responsible for:

- brightness monitoring and control
- media-key interception
- HUD placement
- multi-display behaviour
- True Tone
- Night Shift
- login-item support
- appearance settings
- the About/settings window
- the custom menu bar icon
- command-line building

## Design goal

This fork is intentionally focused.
It is **not** intended to become a full display-management utility.
The goal is simply to bring back the familiar macOS HUD and make it work naturally with a MacBook Pro, Apple Studio Display and Stream Deck, while adding a small set of practical display controls around it.

## Upstream project

This project is based on:
[dannystewart/volumeHUD](https://github.com/dannystewart/volumeHUD)
The original project by Danny Stewart provides the core volumeHUD implementation and deserves the credit for restoring the classic pre-Tahoe macOS HUD.
This fork adds functionality primarily aimed at my own Apple Studio Display and Stream Deck setup.

## License

This fork follows the license of the original volumeHUD project.
See the included `LICENSE` file for details.