# FruitForest - Play on Echo

Play Apple Music in the Amazon Forest.

FruitForest connects Apple Shortcuts to Echo devices through Home Assistant
and Alexa Media Player. Pick a speaker or multi-room group, then send a typed
Apple Music request without speaking to Alexa.

The FruitForest Home Assistant integration is the source of truth for rooms.
Choose Echo devices in a native checklist, assign them to Home Assistant Areas,
and both Shortcuts fetch the current destination list whenever they run.

[Open the visual setup and usage guide](https://play-on-echo-guide.coreypud.chatgpt.site)

## Proven workflows

- **Albums on iPhone:** start a song from the intended album, share the album
  to **Play on Echo**, then choose a room. If iOS omits the shared URL, the
  Shortcut safely uses the current song's album and artist.
- **Typed requests:** run **Echo Quick Play**, enter an album, track, artist,
  or exact playlist name, then choose a room.
- **Shared URLs:** when Apple Music supplies a usable URL, the Shortcut can
  resolve track, album, and playlist metadata through Apple's public lookup
  endpoints.

Apple Music does not consistently pass playlist URLs to Share Sheet
Shortcuts. For playlists, use **Echo Quick Play** with a distinct playlist
name. A dedicated copied-link playlist Shortcut is a planned enhancement.

## Layout

- `custom_components/fruitforest/` — UI-configured Home Assistant integration,
  dynamic target endpoint, playback router, actions, and diagnostics
- `home_assistant/packages/play_on_echo.yaml` — legacy YAML package retained for
  reference and rollback during migration
- `shortcuts/quick-command.md` — build recipe: typed quick-play Shortcut
  (milestone 1 and permanent fallback)
- `shortcuts/play-on-echo.md` — build recipe: the share-sheet Shortcut
- `shortcuts/INSTRUCTIONS.md` — concise usage and troubleshooting guide
- `tools/generate-shortcuts.mjs` — reproducible Shortcut source generator
- `docs/setup.md` — start here: install, auth, probes, verification,
  troubleshooting
- `docs/brainstorms/`, `docs/plans/` — the requirements and implementation
  plan behind this build

## Secrets

The webhook id is the endpoint's only credential. It lives in the HA server's
`secrets.yaml` only — committed files and recipes use
`REPLACE_WITH_LONG_RANDOM_ID` placeholders. Keep it that way.

Signed `.shortcut` files are ignored because private builds can embed the live
webhook URL. Generate them locally and never attach them to a public release.

FruitForest is available under the [MIT License](LICENSE).

## Adding or changing a room

1. In Home Assistant, assign the Echo device to the correct **Area**.
2. Open **Settings → Devices & services → FruitForest → Configure**.
3. Choose **Echo devices**, enable the device, and submit.
4. Run either Shortcut. The updated Area name appears automatically.

Alexa multi-room groups are managed from the same FruitForest configuration
menu. Group names must match the Alexa app exactly.
