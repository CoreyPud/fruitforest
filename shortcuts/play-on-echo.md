# Play on Echo — share-sheet Shortcut build recipe

The verified primary experience: start a song from an album, share that album
from Apple Music, pick a speaker or group, and the album plays. When Apple
Music supplies a usable URL, the same Shortcut can also resolve tracks and
playlists. One Shortcut covers iPhone, iPad, and Mac.

Prerequisites: FruitForest is installed as described in `docs/setup.md`, and
`quick-command.md` is built and verified (it proves the webhook leg this
Shortcut reuses).

## How it resolves metadata (the logic you're about to build)

| Shared URL shape | Content | Resolution |
|---|---|---|
| `.../album/...?i=<id>` or `.../song/.../<id>` | track | iTunes Lookup by track id → `trackName` + `artistName` |
| `.../album/<slug>/<digits>` (no `i=`) | album | iTunes Lookup by album id → `collectionName` + `artistName` |
| `.../playlist/<slug>/pl.*` | playlist | fetch the page → parse `og:title` ("Name by Owner on Apple Music"; editorial playlists omit " by Owner") |

The iTunes Lookup API (`https://itunes.apple.com/lookup?id=<id>`) needs no key
or account. Fallback ladder: Lookup fails → parse `og:title` from the shared
page itself (works for all three types) → last resort, de-hyphenate the URL
slug (lossy — no artist).

## Build steps

Create a new Shortcut named **Play on Echo**.

**Share-sheet configuration (get this right or it won't appear):**
- In the Shortcut's details (ⓘ): enable **Show in Share Sheet**.
- Generated copies must set `WFWorkflowHasShortcutInputVariables` to `true`;
  otherwise iOS imports `Shortcut Input` as a blank generic `Input`.
- Share Sheet Types: choose **Select All**. Apple Music can provide an iTunes
  product or media share object on iOS rather than a bare URL; limiting the
  shortcut to URLs discards that input before the first action runs.
- macOS additionally needs **Use as Quick Action** and **Show in Share Sheet**
  enabled, plus the Shortcuts sharing extension in System Settings.

**Actions in order:**

1. **Get URLs from Input** must be the first action, with no manually assigned
   input variable. Shortcuts then supplies Shortcut Input through the native
   first-action pipeline and extracts the link from either a URL or Apple
   Music's richer share object when iOS exposes one. Generated
   `ExtensionInput` tokens are not reliably recognized after import.

   Count the URLs immediately. If the count is zero, use **Get Current Song**,
   then **Get Details of Music** for `Album` and `Artist`. Apple Music on iOS
   can invoke a share-sheet Shortcut without supplying a coercible URL; this
   fallback is the verified native metadata path. If there is also no current
   song, show **Nothing sent** and stop before the room picker or webhook.
   Start a song from the album before sharing so the fallback identifies the
   intended album.

2. **Get First Item from List** (on the result of step 1) — uses the canonical
   `music.apple.com` URL supplied by Apple Music's share sheet. Avoid **Expand
   URL** here; on macOS it can stall indefinitely for otherwise valid Apple
   Music URLs.

3. **Branch by URL shape.** Use *Match Text* (regex) on the expanded URL, with
   an If block per case:

   **Case track — regex `[?&]i=(\d+)` matches, or URL contains `/song/`:**
   - Track id = the captured `i=` digits (for `/song/` URLs: *Match Text*
     `/song/[^/]+/(\d+)` and take group 1).
   - **Get Contents of URL**: `https://itunes.apple.com/lookup?id=<track id>`
     (GET).
   - **Get Dictionary from Input**, then get `results` → first item.
   - title = `trackName`, artist = `artistName`, kind = `track`.

   **Case album — regex `/album/[^/]+/(\d+)(?!.*[?&]i=)` (an `/album/` URL
   with trailing digits and no `i=` parameter anywhere in the query). Build
   the If blocks in this order — track first — so a track URL can never fall
   through to the album case:**
   - Album id = captured digits.
   - Lookup as above; title = `collectionName`, artist = `artistName`,
     kind = `album`.

   **Case playlist — URL contains `/playlist/`:**
   - **Get Contents of URL** on
     `https://music.apple.com/api/oembed?url=<shared URL>` (GET).
   - **Get Dictionary from Input**, then get the `title` value as the playlist
     name. This avoids brittle HTML scraping and works for personal and
     editorial playlists.
   - kind = `playlist`. Works for personal `pl.u-` links (public once shared).

4. **Fallback guard.** If the URL is not a recognized track, album, or
   playlist shape, send it as `freeform`. Home Assistant still receives a
   visible request instead of the shortcut failing silently.

5. **Load and choose a destination.** Use **Get Contents of URL** with the
   FruitForest webhook and method `GET`, convert the response to a Dictionary,
   get its `targets` value, then pass that value to **Choose from List**. Both
   Shortcuts now receive the same live destination list from Home Assistant.

6. **Dictionary**
   - `kind`: from the matched case
   - `title` / `artist`: for track/album cases
   - `name`: for the playlist case
   - `target`: *Chosen Item*
   - `sender`: your companion-app slug
   (Dictionary action always — titles like `Take On Me (1985 12" Mix)` break
   hand-assembled JSON.)

7. **Get Contents of URL** — POST, JSON body, to
   `http://YOUR_HA_HOST:8123/api/webhook/REPLACE_WITH_LONG_RANDOM_ID`
   (keep the real id out of commits and screenshots).

8. **Show Notification** — Title `Sent to Echo`, body showing what → where.
   Delivery confirmation only; playback failures arrive via HA notifications.

## Automation surface (zero-prompt invocation)

To let other Shortcuts and personal automations start music without prompts
(e.g., a morning routine playing a playlist in the kitchen):

- In this Shortcut, steps 5 (picker) and 1–4 (URL parsing) only run when their
  inputs are missing. The simplest robust pattern: create a tiny companion
  Shortcut per automation — a **Dictionary** with the preset payload
  (`kind: playlist, name: Sunday Morning, target: kitchen, sender: …`)
  followed by the same **Get Contents of URL** POST. Two actions, no prompts,
  same webhook, same router.
- Any HA automation can also call `fruitforest.play` directly with the same
  fields — no Shortcut involved at all.

## Verify (from the plan's acceptance checklist)

- Share a **track** (URL will contain `?i=`) → exact track + artist plays on
  the chosen Echo.
- Share an **album** to a group target → whole group plays in sync.
- Share a **personal playlist** (`pl.u-` link) → correct playlist starts.
- Share an **editorial playlist** (`pl.` link) → name parses (no owner
  segment).
- Share from a **non-US storefront** URL or a storefront-less URL → resolves
  after Expand URL.
- Point the Lookup URL at an invalid host once → og:title fallback still
  produces title + artist.
- Kill Wi-Fi → visible Shortcuts error alert.
- Share a track from **macOS Music** (`···` → Share) → plays.
