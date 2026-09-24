#!/bin/zsh
set -euo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

APP_VERSION="3.3.3"
BUILD_NUMBER="3"

echo "== volumeHUD command-line build v4 =="
echo "Source: $ROOT"
echo

if [[ ! -d "volumeHUD" ]]; then
  echo "ERROR: map 'volumeHUD' niet gevonden."
  echo "Voer dit script uit vanuit de hoofdmap volumeHUD-3.3.3."
  exit 1
fi

DEV="$(xcode-select -p 2>/dev/null || true)"
if [[ -z "$DEV" || ! -d "$DEV" ]]; then
  echo "ERROR: Apple Command Line Tools zijn niet geïnstalleerd."
  echo "Installeer ze met:"
  echo "  xcode-select --install"
  exit 1
fi

SWIFTC="$DEV/usr/bin/swiftc"
SDKROOT_DIR="$DEV/SDKs"

if [[ ! -x "$SWIFTC" ]]; then
  echo "ERROR: swiftc niet gevonden op $SWIFTC"
  exit 1
fi

echo "Developer tools: $DEV"
echo "Swift compiler: $SWIFTC"
"$SWIFTC" --version | head -n 2
echo

echo "Beschikbare macOS SDK's:"
for sdk in "$SDKROOT_DIR"/MacOSX*.sdk(N); do
  echo "  $(basename "$sdk") -> $sdk"
done
echo

if [[ -d "$SDKROOT_DIR/MacOSX26.5.sdk" ]]; then
  SDK="$SDKROOT_DIR/MacOSX26.5.sdk"
elif [[ -d "$SDKROOT_DIR/MacOSX26.sdk" ]]; then
  SDK="$SDKROOT_DIR/MacOSX26.sdk"
else
  CANDIDATES=( "$SDKROOT_DIR"/MacOSX26.*.sdk(N) )
  if (( ${#CANDIDATES[@]} == 0 )); then
    echo "ERROR: Geen macOS 26 SDK gevonden."
    exit 2
  fi
  SDK="${CANDIDATES[-1]}"
fi

echo "Gekozen SDK: $SDK"
echo

BUILDROOT="$ROOT/build-cli"
SRCDIR="$BUILDROOT/src"
APP="$BUILDROOT/volumeHUD.app"
CONTENTS="$APP/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

rm -rf "$BUILDROOT"
mkdir -p "$SRCDIR" "$MACOS" "$RESOURCES"

# Werk alleen op een tijdelijke kopie.
cp "$ROOT"/volumeHUD/*.swift "$SRCDIR"/

echo "CLT-compatibiliteitsaanpassingen maken in tijdelijke bronkopie..."

python3 - "$SRCDIR" <<'PY'
from pathlib import Path
import re
import sys

src = Path(sys.argv[1])

# @Entry -> klassieke EnvironmentKey-implementatie
login = src / "LoginItemManager.swift"
text = login.read_text(encoding="utf-8")

pattern = re.compile(
    r'''extension\s+EnvironmentValues\s*\{\s*
        @Entry\s+var\s+loginItemManager\s*:\s*LoginItemManager\?\s*
        \}''',
    re.VERBOSE,
)

replacement = '''private struct LoginItemManagerKey: EnvironmentKey {
    static let defaultValue: LoginItemManager? = nil
}

extension EnvironmentValues {
    var loginItemManager: LoginItemManager? {
        get { self[LoginItemManagerKey.self] }
        set { self[LoginItemManagerKey.self] = newValue }
    }
}'''

text2, count = pattern.subn(replacement, text, count=1)
if count != 1:
    print("ERROR: verwachte @Entry loginItemManager niet exact één keer gevonden.", file=sys.stderr)
    sys.exit(10)

login.write_text(text2, encoding="utf-8")
print("  OK: @Entry vervangen door EnvironmentKey")


def remove_one_preview(text: str):
    """Verwijder het eerste complete #Preview(...) { ... } blok."""
    m = re.search(r'(?m)^[ \t]*#Preview(?:\s*\([^\n{]*\))?\s*\{', text)
    if not m:
        return text, False

    brace = text.find("{", m.start(), m.end())
    if brace < 0:
        raise RuntimeError("openingsaccolade van #Preview niet gevonden")

    depth = 0
    i = brace
    in_string = False
    in_multiline_string = False
    escape = False
    line_comment = False
    block_comment = 0

    while i < len(text):
        # Triple-quoted strings
        if not line_comment and block_comment == 0:
            if not in_string and text.startswith('"""', i):
                in_multiline_string = not in_multiline_string
                i += 3
                continue

        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_multiline_string:
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
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
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
                end = i + 1
                # Neem aansluitende lege regel/newline mee.
                while end < len(text) and text[end] in " \t":
                    end += 1
                if end < len(text) and text[end] == "\n":
                    end += 1
                return text[:m.start()] + text[end:], True

        i += 1

    raise RuntimeError("einde van #Preview-blok niet gevonden")


# Verwijder ALLE #Preview-blokken uit ALLE tijdelijke Swift-bestanden.
preview_total = 0
for path in sorted(src.glob("*.swift")):
    text = path.read_text(encoding="utf-8")
    removed_here = 0

    while "#Preview" in text:
        text2, removed = remove_one_preview(text)
        if not removed:
            print(f"ERROR: '#Preview' aangetroffen maar niet parseerbaar in {path.name}", file=sys.stderr)
            sys.exit(11)
        text = text2
        removed_here += 1
        preview_total += 1

    if removed_here:
        path.write_text(text, encoding="utf-8")
        print(f"  OK: {removed_here} #Preview-blok(ken) verwijderd uit {path.name}")

print(f"  Totaal verwijderde #Preview-blokken: {preview_total}")
PY

setopt null_glob
SOURCES=( "$SRCDIR"/*.swift )

echo
echo "Swift-bestanden: ${#SOURCES[@]}"
echo "Compileren tegen $(basename "$SDK")..."
echo

"$SWIFTC" \
  -swift-version 6 \
  -O \
  -sdk "$SDK" \
  "${SOURCES[@]}" \
  -o "$MACOS/volumeHUD"

cat > "$CONTENTS/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleExecutable</key>
  <string>volumeHUD</string>
  <key>CFBundleIdentifier</key>
  <string>com.dannystewart.volumehud.custom</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>volumeHUD</string>
  <key>CFBundleDisplayName</key>
  <string>volumeHUD</string>
  <key>CFBundleIconFile</key>
  <string>volumeHUD</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>$APP_VERSION</string>
  <key>CFBundleVersion</key>
  <string>$BUILD_NUMBER</string>
  <key>LSUIElement</key>
  <true/>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
</dict>
</plist>
PLIST

# Neem projectresources mee in de appbundle VOORDAT de app wordt ondertekend.
if [[ -d "$ROOT/volumeHUD/Resources" ]]; then
  echo
  echo "Resources kopiëren..."
  cp -R "$ROOT/volumeHUD/Resources/." "$RESOURCES/"
fi

# ------------------------------------------------------------
# App icon
# ------------------------------------------------------------

ICON_SOURCE="$ROOT/resources/volumeHUD.png"
ICONSET="$BUILDROOT/volumeHUD.iconset"
ICON_ICNS="$ROOT/resources/volumeHUD.icns"

echo
echo "App icon maken..."

rm -rf "$ICONSET"
mkdir -p "$ICONSET"

sips -z 16 16     "$ICON_SOURCE" --out "$ICONSET/icon_16x16.png" >/dev/null
sips -z 32 32     "$ICON_SOURCE" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
sips -z 32 32     "$ICON_SOURCE" --out "$ICONSET/icon_32x32.png" >/dev/null
sips -z 64 64     "$ICON_SOURCE" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
sips -z 128 128   "$ICON_SOURCE" --out "$ICONSET/icon_128x128.png" >/dev/null
sips -z 256 256   "$ICON_SOURCE" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
sips -z 256 256   "$ICON_SOURCE" --out "$ICONSET/icon_256x256.png" >/dev/null
sips -z 512 512   "$ICON_SOURCE" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
sips -z 512 512   "$ICON_SOURCE" --out "$ICONSET/icon_512x512.png" >/dev/null
sips -z 1024 1024 "$ICON_SOURCE" --out "$ICONSET/icon_512x512@2x.png" >/dev/null

iconutil -c icns "$ICONSET" -o "$ICON_ICNS"

cp "$ICON_ICNS" "$RESOURCES/volumeHUD.icns"

echo "App icon geïnstalleerd."

echo
echo "Ad-hoc ondertekenen..."
codesign --force --deep --sign - "$APP"

echo
echo "KLAAR:"
echo "  $APP"
echo
echo "Start met:"
echo "  open \"$APP\""
echo
echo "De originele Swift-bronbestanden zijn NIET gewijzigd door dit buildscript."
