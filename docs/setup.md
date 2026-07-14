# FruitForest setup and maintenance

FruitForest lets Apple Shortcuts send exact Apple Music requests to Echo
devices through Home Assistant and Alexa Media Player. Home Assistant owns the
destination list; the Shortcuts download that list each time they run.

## Prerequisites

- Home Assistant 2026.7 or later, reachable from household devices
- HACS
- Alexa Media Player, signed in and exposing each Echo as `media_player.*`
- Apple Music enabled and linked in the Alexa app
- Home Assistant Areas matching the room names you want to see

## Install FruitForest with HACS

Until FruitForest is listed in HACS's default catalog, add it as a custom
repository:

1. Open **HACS → Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Enter `https://github.com/CoreyPud/fruitforest` and choose **Integration**.
4. Install **FruitForest**, then restart Home Assistant.
5. Open **Settings → Devices & services → Add integration → FruitForest**.

The setup screen contains:

- **Echo devices**: a multi-select checklist. Enable only speakers that should
  appear in the Shortcuts.
- **Shortcut webhook ID**: a private random identifier used by the local
  Shortcut endpoint. Keep the generated value, or paste the existing
  `play_on_echo_webhook_id` while migrating.

FruitForest uses each selected entity's Home Assistant Area as its display
name. When an entity has no Area, it uses the entity's friendly name.

## Migrate from the YAML package

The old package and the integration cannot own the same webhook ID at the same
time. Use this order:

1. Note the current `play_on_echo_webhook_id` from Home Assistant's
   `secrets.yaml`.
2. Disable the **Play on Echo — webhook receiver** automation.
3. Restart Home Assistant so the old webhook registration is released.
4. Add the FruitForest integration and paste the existing webhook ID.
5. Select the Echo entities that should appear.
6. Add Alexa groups under **FruitForest → Configure**.
7. Replace both Shortcuts with dynamic FruitForest builds.
8. Test one single Echo and one Alexa group.
9. Remove `packages/play_on_echo.yaml` from the Home Assistant configuration
   after the tests pass.

Using the existing webhook ID keeps the endpoint URL unchanged. The Shortcuts
still need to be replaced once because the new builds perform a `GET` before
playback to retrieve the current target list.

## Assign Echo devices to rooms

For each Echo:

1. Open **Settings → Devices & services → Alexa Media Player**.
2. Open the Echo device.
3. Assign its **Area**, such as **Kitchen**, **Office**, or **Living Room**.
4. Open **Settings → Devices & services → FruitForest → Configure**.
5. Choose **Echo devices**, enable it, and submit.

The new Area name appears in **Play on Echo** and **Echo Quick Play** the next
time either Shortcut runs. There is no Shortcut list to edit.

If two enabled Echos share the same Area, FruitForest appends each entity's
friendly name so the picker remains unambiguous.

## Add an Alexa speaker group

Alexa groups are not Home Assistant Areas. They remain explicit because Alexa
requires the group's exact spoken name and a carrier Echo.

1. Open **Settings → Devices & services → FruitForest → Configure**.
2. Choose **Add or update an Alexa group**.
3. Enter the group name exactly as shown in the Alexa app, such as
   `Everywhere`.
4. Choose a reliably powered Echo as the carrier.
5. Submit, then run a Shortcut to see the group.

Adding the same group name again updates its carrier. Use **Remove an Alexa
group** to delete it.

## Test from Home Assistant

Open **Developer tools → Actions** and run `fruitforest.play`:

```yaml
action: fruitforest.play
data:
  kind: album
  title: Rumours
  artist: Fleetwood Mac
  target: Living Room
```

To inspect the destination list without sending music, run
`fruitforest.get_targets` with response data enabled.

Test these cases after setup or an Alexa Media Player update:

1. A track or album on a single Echo.
2. A typed playlist request with a distinctive playlist name.
3. An Alexa multi-room group.
4. An unavailable Echo, which should produce a FruitForest notification.

## Build the Shortcuts

Generate public placeholder sources:

```sh
node tools/generate-shortcuts.mjs
node tools/test-generated-shortcuts.mjs
```

For a private build, provide the local webhook URL and optional companion-app
sender slug:

```sh
PLAY_ON_ECHO_WEBHOOK_URL='http://homeassistant.local:8123/api/webhook/YOUR_ID' \
PLAY_ON_ECHO_SENDER='coreys_iphone' \
node tools/generate-shortcuts.mjs
```

The webhook is local-only. The ID is the endpoint credential, so never commit
the private generated Shortcut files or the real URL.

## Day-to-day maintenance

### Add or replace an Echo

Assign its Area, enable it in the FruitForest checklist, and test it. No
Shortcut rebuild is required.

### Rename a room

Rename the Home Assistant Area. FruitForest uses the new name immediately.

### Remove an Echo

Disable it in **FruitForest → Configure → Echo devices**. Removing it from
Alexa Media Player alone leaves a stale selection that diagnostics will show
as unavailable.

### Alexa Media Player needs authentication

Reconfigure Alexa Media Player under **Settings → Devices & services**. A
FruitForest target marked unavailable usually means its selected media-player
entity is unavailable or was replaced during reauthentication.

### Shortcuts cannot load rooms

Confirm the phone is on the home network and Home Assistant is reachable at
the URL embedded in the Shortcut. A dynamic Shortcut requires FruitForest's
`GET` endpoint; the old YAML webhook accepts only `POST`.

### Alexa plays the wrong playlist

Use **Echo Quick Play** and include a distinctive playlist name. Apple Music's
Share Sheet still does not consistently provide playlist URLs, and Alexa may
prefer public playlists with generic names.

## Diagnostics and removal

Download diagnostics from **Settings → Devices & services → FruitForest →
Download diagnostics**. The webhook ID is redacted. Diagnostics include the
selected entities, current names, destination types, and availability.

To remove FruitForest, delete its config entry, remove the HACS integration,
restart Home Assistant, and delete the two Shortcuts. The integration does not
modify Alexa devices, Home Assistant Areas, or Apple Music.
