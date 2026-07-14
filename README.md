# FruitForest - Play on Echo

Play Apple Music in the Amazon Forest.

FruitForest connects Apple Shortcuts to Echo devices through Home Assistant
and Alexa Media Player. Pick a speaker or multi-room group, then send a typed
Apple Music request without speaking to Alexa.

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

- `home_assistant/packages/play_on_echo.yaml` — webhook receiver + play-router
  script for Home Assistant (edit the target maps for your devices)
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
