# fruitforrest — Play on Echo

Browse Apple Music on iPhone, iPad, or Mac; share to a Shortcut; pick an Echo
device or Alexa speaker group; the exact music plays. A household bridge that
replaces Alexa's lossy voice channel with exact typed metadata, using Home
Assistant and the Apple Music skill on Alexa as the playback engine.

## Layout

- `home_assistant/packages/play_on_echo.yaml` — webhook receiver + play-router
  script for Home Assistant (edit the target maps for your devices)
- `shortcuts/quick-command.md` — build recipe: typed quick-play Shortcut
  (milestone 1 and permanent fallback)
- `shortcuts/play-on-echo.md` — build recipe: the share-sheet Shortcut
- `docs/setup.md` — start here: install, auth, probes, verification,
  troubleshooting
- `docs/brainstorms/`, `docs/plans/` — the requirements and implementation
  plan behind this build

## Secrets

The webhook id is the endpoint's only credential. It lives in the HA server's
`secrets.yaml` only — committed files and recipes use
`REPLACE_WITH_LONG_RANDOM_ID` placeholders. Keep it that way.
