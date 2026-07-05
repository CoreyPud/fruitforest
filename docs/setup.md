# Play on Echo — Setup Guide

Browse in Apple Music, share to a Shortcut, pick a speaker, and the exact music
plays on your Echo — no voice mishearing. This guide takes you from a bare Home
Assistant install to working share-sheet playback on iPhone, iPad, and Mac.

Order matters: each stage builds on the previous one.

## Prerequisites

- Home Assistant server reachable from your household devices
- Apple Music skill linked to Alexa (Alexa app → More → Skills → Apple Music),
  with your Apple Music subscription on the account linked there
- Alexa speaker groups defined in the Alexa app (e.g., "Everywhere")
- HACS installed in Home Assistant
- Home Assistant companion app on the phones/tablets that should receive
  failure notifications

## Stage 1 — Alexa Media Player integration

1. HACS → search **Alexa Media Player** → install → restart HA.
2. Amazon requires app-based 2FA for this integration. On the Amazon account:
   open `https://www.amazon.com/a/settings/approval`, add an **authenticator
   app**, and copy the **52-character app key** shown during setup — the
   integration uses it to generate OTPs for silent re-login.
3. Settings → Devices & Services → Add Integration → Alexa Media Player.
   Log in through the built-in proxy; paste the 52-character key in the
   Built-in 2FA App Key field.
4. Confirm every Echo appears as a `media_player.*` entity. Record the entity
   ids here:

   | Room | Entity id |
   |------|-----------|
   | Kitchen | `media_player.kitchen_echo` (example — replace) |
   | Office | `media_player.office_echo` (example — replace) |

   Security note: after this stage, HA's config holds everything needed to log
   into the Amazon account. Household-acceptable by decision; keep HA itself
   access-controlled.

## Stage 2 — Probes (run before installing anything else)

Run these from **Developer Tools → Actions**. They de-risk the two unknowns the
whole design rests on, and their results feed the package config in Stage 3.

**Probe A — single device, Apple Music provider:**

```yaml
action: media_player.play_media
target:
  entity_id: media_player.kitchen_echo   # one of yours
data:
  media_content_type: APPLE_MUSIC
  media_content_id: "Songbird by Fleetwood Mac"
```

Expected: that exact track plays on that Echo. This confirms the provider-typed
channel works against your account.

**Probe B — group playback phrasing.** Try both, note which works:

```yaml
# B1: typed text command (the type-to-Alexa pipeline; the safer bet)
action: media_player.play_media
target:
  entity_id: media_player.kitchen_echo   # any single Echo
data:
  media_content_type: custom
  media_content_id: "play the album Rumours by Fleetwood Mac on apple music on Everywhere"

# B2: provider call with group suffix (undocumented; test it)
action: media_player.play_media
target:
  entity_id: media_player.kitchen_echo
data:
  media_content_type: APPLE_MUSIC
  media_content_id: "the album Rumours by Fleetwood Mac in the Everywhere group"
```

Expected: all Echos in the group play in sync. Record the winner:

> Group phrasing result: _____________ (date: _______)
> Does the carrier Echo speak an audible acknowledgment? ______

The shipped package uses the B1 text-command form for groups. If only B2
worked, adjust the group branch in `play_on_echo.yaml` accordingly.

**Probe C — negative probe.** Send a nonsense phrase
(`media_content_id: "xqzzt blorp"` with `APPLE_MUSIC`) and observe what the
Echo does (silence vs. spoken error). This tells you what a fuzzy-search miss
looks like so you can recognize it later.

**Probe D — fallback rehearsal (do not skip).** The community integration
breaks every month or two when Amazon changes things; the rehearsed fallback is
the official core **Alexa Devices** integration (HA 2025.6+):

1. Settings → Devices & Services → Add Integration → **Alexa Devices**
   (same app-2FA requirement).
2. Run its text command against one Echo and one group:

   ```yaml
   action: alexa_devices.send_text_command
   data:
     text: "play Songbird by Fleetwood Mac on apple music"
     # target per the integration's docs — record what worked
   ```

3. Record the working phrasing and auth steps here:

   > Core integration result: _____________ (date: _______)

If Alexa Media Player breaks for an extended period, the swap is: replace the
router script's two `media_player.play_media` calls with
`alexa_devices.send_text_command` calls carrying the same phrases. No Shortcut
changes needed.

## Stage 3 — Install the package

1. Enable packages in `configuration.yaml` if not already:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

2. Copy `home_assistant/packages/play_on_echo.yaml` from this repo into
   `<config>/packages/`.
3. Generate a long random webhook id and add it to `<config>/secrets.yaml`:

   ```bash
   openssl rand -hex 24
   ```

   ```yaml
   # secrets.yaml — lives on the HA server ONLY
   play_on_echo_webhook_id: <the random value>
   ```

   **Never put the real webhook id in this repo, in the Shortcut recipes, or
   in screenshots.** It is the endpoint's only credential; anything committed
   here should show `REPLACE_WITH_LONG_RANDOM_ID`. Note the endpoint is
   reachable by any device on your LAN — the id being long and random is the
   protection, so treat it like a password.

4. Edit the `device_map` and `group_map` in the package to match your Stage 1
   inventory. For each group, pick the **carrier** — your most reliably powered
   Echo. Group commands are issued through it; if it's unplugged, group sends
   fail even when the rest of the group is fine.
5. Restart HA (or reload automations + scripts).
6. Smoke-test the webhook from any machine on your network:

   ```bash
   curl -X POST http://<ha-host>:8123/api/webhook/REPLACE_WITH_LONG_RANDOM_ID \
     -H 'Content-Type: application/json' \
     -d '{"kind":"track","title":"Songbird","artist":"Fleetwood Mac","target":"kitchen"}'
   ```

   Then verify the failure paths: an unknown target
   (`"target":"garage"`) should produce a "Play on Echo failed" persistent
   notification listing known targets, and a payload with a missing artist
   should still play (title-only phrase).

## Stage 4 — Shortcuts

Build in this order:

1. `shortcuts/quick-command.md` — the typed quick-command (proves the whole
   pipeline end to end; also your fallback entry point).
2. `shortcuts/play-on-echo.md` — the share-sheet Shortcut (the main event).

Both recipes send an optional `sender` field. Set it to your phone's
companion-app slug (Settings → Companion App → the name after
`notify.mobile_app_`) so failures push to the device that sent the request.
The Shortcut's own "Sent" notification only confirms delivery to HA — playback
failures arrive via HA notifications, because the webhook acknowledges before
Alexa is contacted.

## Stage 5 — macOS

The Mac's Music app shares the same `music.apple.com` URL as iOS, so the same
Shortcut works unchanged. Two one-time switches, without which it will not
appear at all:

1. In Shortcuts (macOS): open Play on Echo → details (ⓘ) → enable
   **Use as Quick Action** and **Show in Share Sheet** (wording varies slightly
   by macOS version).
2. System Settings → General → Login Items & Extensions → Extensions →
   Sharing → enable **Shortcuts**.

Then in Music: select a track/album/playlist → `···` → Share → Play on Echo.

## Device-change checklist

The target list lives in **two places by design** — the HA target map is
canonical, and each Shortcut carries a static picker copy. When you add,
remove, or rename an Echo or group:

1. Update `device_map` / `group_map` in `<config>/packages/play_on_echo.yaml`
   (and mirror the edit in this repo's copy).
2. Update the picker list in the quick-command Shortcut.
3. Update the picker list in the Play on Echo Shortcut.
4. Send a test to the changed target.

Skipping a Shortcut edit produces either a picker entry HA rejects (you'll get
the unknown-target notification) or a missing new device.

## Troubleshooting

- **Sends succeed but nothing plays, no notification** — likely a fuzzy-search
  miss (compare with Probe C behavior). Check the persistent notifications in
  HA; if none, the phrase reached Alexa but matched something odd. Try the
  quick-command Shortcut with a more specific phrase.
- **"unavailable" failure notifications** — Alexa Media Player lost auth.
  Settings → Devices & Services → Alexa Media Player → Reconfigure. If HA was
  restarted and login loops: delete `<config>/alexa_media.<email>.pickle` and
  restart. Breakage after Amazon-side changes typically has a fix within days —
  check the integration's GitHub issues, and remember Probe D's rehearsed
  fallback.
- **Shortcut shows its own error alert** — the POST never reached HA (wrong
  host, HA down, or not on home Wi-Fi with `local_only: true`). Remote sends
  from cellular require the Nabu Casa webhook URL and `local_only: false` —
  a deliberate exposure decision, deferred until wanted.
- **Playlist plays the wrong thing** — generic playlist names ("Chill") can
  lose to Apple Music editorial playlists in Alexa's search. Rename the
  playlist to something distinctive.
