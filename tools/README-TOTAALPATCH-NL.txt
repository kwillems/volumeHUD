volumeHUD 3.3.3 — totaalpatch

DOEL
Deze patch is bedoeld voor een SCHONE, originele volumeHUD 3.3.3-bronmap.

BEVAT
- Apple Studio Display brightness via DisplayServices
- Stream Deck System > Multimedia brightness up/down
- Stream Deck volume up/down/mute
- deduplicatie van dubbele synthetische Stream Deck-media-events
- brightness-HUD op het bedoelde scherm
- HUD Follows Mouse geldt voor zowel Volume HUD als Brightness HUD
- menu-baritem dat About/settings opent
- definitief custom menu-baricoon:
  speaker + monitor + 7 blokjes, waarvan 5 donker en 2 licht
- True Tone-schakelaar in About
- live synchronisatie van True Tone met Systeeminstellingen
- uitlijning van de True Tone-toggle
- command-line buildscript voor Apple Command Line Tools

BEWUST NIET OPGENOMEN
- Automatically adjust brightness / Automatic Brightness.
  De eerdere experimenten hiervoor zijn niet onderdeel van deze totaalpatch.

TOEPASSEN
1. Pak deze ZIP uit.
2. Ga in Terminal naar de SCHONE originele volumeHUD-3.3.3-map.
3. Voer uit:

   python3 /pad/naar/patch_volumehud_v3_3_3_totaal.py .

4. Kopieer daarna het meegeleverde buildscript naar de projectmap:

   cp /pad/naar/build_volumehud_cli_v4.sh ./build_volumehud_cli_v4.sh
   chmod +x ./build_volumehud_cli_v4.sh

5. Bouw:

   ./build_volumehud_cli_v4.sh

6. Start:

   killall volumeHUD 2>/dev/null
   open ./build-cli/volumeHUD.app

BELANGRIJK
De custom app gebruikt bundle-id:
com.dannystewart.volumehud.custom

Na een nieuwe ad-hoc build kan macOS opnieuw toestemming vereisen voor:
- Toegankelijkheid
- Invoermonitoring

Als Stream Deck brightness/volume na een rebuild niet reageert, controleer deze permissies eerst.

Het buildscript kopieert Resources/MenuBarIcon.svg nu VOOR codesign naar de appbundle.
Daardoor blijft het custom menu-baricoon onderdeel van een correct opnieuw ondertekende build.

BACK-UP
De patch maakt vóór wijziging een patch-backup-original-map in het project.
