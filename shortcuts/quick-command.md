# Quick Command — Shortcut build recipe

Type what you want, pick a speaker, music plays. This is the first milestone
(it proves the whole pipeline with no URL parsing) and the permanent fallback
when sharing isn't handy. Works unchanged on iPhone, iPad, and Mac.

Prerequisite: Stage 3 of `docs/setup.md` complete (webhook live, smoke-tested).

## Build steps

Create a new Shortcut named **Echo Quick Play**, then add these actions in
order:

1. **Ask for Input**
   - Prompt: `Play what?`
   - Input type: Text
   - (The text goes to Alexa verbatim — phrase it like a request:
     `the album Rumours by Fleetwood Mac`, `my playlist Sunday Morning`.)

2. **Choose from List**
   - List items: your target names, exactly matching the `device_map` /
     `group_map` keys in the HA package — e.g. `kitchen`, `office`, `bedroom`,
     `everywhere`.
   - Prompt: `Play where?`

3. **Dictionary**
   - `kind` (Text): `freeform`
   - `title` (Text): *Provided Input* (magic variable from step 1)
   - `target` (Text): *Chosen Item* (magic variable from step 2)
   - `sender` (Text): your companion-app slug, e.g. `coreys_iphone`
     (see Stage 4 of `docs/setup.md`; leave out if you don't use the
     companion app)

   Always build the body with a Dictionary action — never by assembling JSON
   text, since titles can contain quotes and brackets.

4. **Get Contents of URL**
   - URL: `http://YOUR_HA_HOST:8123/api/webhook/REPLACE_WITH_LONG_RANDOM_ID`
   - Method: `POST`
   - Request Body: `JSON` → *Dictionary* (magic variable from step 3)
   - (Shortcuts sets `Content-Type: application/json` automatically for JSON
     bodies. Keep the real webhook id out of anything you commit or
     screenshot.)

5. **Show Notification**
   - Title: `Sent to Echo`
   - Body: `Provided Input` → `Chosen Item` (e.g. shows
     "the album Rumours… → kitchen")
   - This confirms **delivery to HA only**. Playback problems (Alexa auth
     expired, unknown target) arrive as HA notifications a moment later.

## Failure behavior (by design)

- **HA unreachable** (wrong host, HA down, not on home Wi-Fi): step 4 fails
  and Shortcuts shows its own error alert — the visible failure required by
  the plan. Nothing to build; just don't wrap step 4 in error suppression.
- **HA reached but playback failed**: HA pushes a "Play on Echo failed"
  notification to your `sender` device and records a persistent notification.

## Verify

- Type `the album Rumours by Fleetwood Mac`, target `kitchen` → plays within
  ~10 seconds.
- Turn off Wi-Fi, repeat → Shortcuts error alert appears.
- Target a made-up name (add `garage` to the list temporarily) → HA
  "unknown target" notification arrives; no play attempt.
