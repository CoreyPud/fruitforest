# Play on Echo — share-sheet Shortcut build recipe

The primary experience: share a track, album, or playlist from Apple Music,
pick a speaker or group, and the exact music plays. One Shortcut covers
iPhone, iPad, and Mac — the Music app hands over the same `music.apple.com`
URL on all three.

Prerequisites: Stage 3 of `docs/setup.md` complete; `quick-command.md` built
and verified (it proves the webhook leg this Shortcut reuses).

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
- Share Sheet Types: select **URLs** only. Do NOT select "Media" — that means
  audio/video *files* and will prevent the Shortcut from appearing for Apple
  Music shares.
- macOS additionally needs the extension switches — Stage 5 of `docs/setup.md`.

**Actions in order:**

1. **Get URLs from Input** (input: Shortcut Input) — normalizes the share
   payload to a URL.

2. **Expand URL** (on the result of step 1) — resolves `geo.music.apple.com`
   affiliate-style links, storefront-less URLs, legacy `itunes.apple.com`
   links, and shortener wrappers to the final `music.apple.com` URL before any
   parsing.

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
   - **Get Contents of URL** on the expanded URL itself (GET).
   - **Match Text** on the page HTML:
     `og:title" content="(.*) on Apple Music"`
   - Take capture group 1, then — only if it contains ` by ` — split on the
     **last** ` by ` and keep the left side as the name (the right side is
     the owner). Splitting on the last occurrence keeps names that themselves
     contain " by " intact ("Songs by the Sea by Corey" → "Songs by the Sea").
     Editorial `pl.` playlists have no owner segment; if an editorial name
     itself ends in " by …" the split over-trims — rename or use the
     quick-command Shortcut for that one.
   - kind = `playlist`. Works for personal `pl.u-` links (public once shared).

4. **Fallback guard.** After the track/album lookups, add an If: if `title`
   *has no value* (Lookup empty or unreachable), fetch the expanded URL and
   parse `og:title` exactly as in the playlist case — track/album pages carry
   it too ("Title by Artist on Apple Music"; the last-` by `-split's right
   side IS the artist here). If that also fails, take the URL's slug segment,
   replace `-` with spaces, and use it as `title` with no artist.

5. **Choose from List** — same target list as the quick-command Shortcut
   (must match the HA target map; see the device-change checklist in
   `docs/setup.md`).

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
- Any HA automation can also call `script.play_on_echo` directly with the same
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
