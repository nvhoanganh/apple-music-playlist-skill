---
name: applemusic-playlist
description: Search Apple Music catalog and add songs to a playlist in the local Music.app on macOS. Use when the user gives a list of "Artist - Title" songs and wants them found and added to an Apple Music playlist, or mentions building/updating an Apple Music playlist. Handles songs not yet in the library by adding them via the Apple Music API first, then sweeping into the named playlist. Requires macOS with Music.app and an Apple Music subscription.
---

# Apple Music Playlist Builder

Turn a list of `Artist - Title` lines into a Music.app playlist. Songs already in
the library are added directly; songs only in the catalog are added to the iCloud
library via the Apple Music API first, then swept into the playlist.

**No Apple Developer account needed.** A hosted server provides the developer token.
You bring only your Apple Music subscription.

## Setup (once)

1. **macOS** with Music.app signed into your Apple Music account.
2. `python3 -m pip install --user certifi` (once).
3. Set your country in `config.json` (`storefront`: `au`, `us`, `gb`, ...). The
   `server_url` is preconfigured to the hosted dev-token server.

## Get your Music User Token (expires ~6 months)

```
cd ~/.claude/skills/applemusic-playlist
python3 scripts/get_token.py
```

Opens https://applemusicplaylist.onrender.com/authorize — sign in, the token is
shown and auto-copied → paste it into `user_token.txt` in this folder.

If API calls later return HTTP 401/403, the token expired — rerun this.

## Add songs to a playlist

Songs file, one per line as `Artist - Title` (`#` comments ok):

```
Dire Straits - Iron Hand
Neil Young - Heart of Gold
John Mayer - Slow Dancing in a Burning Room (Acoustic)
```

Then:

```
python3 scripts/add_songs.py "My Playlist Name" songs.txt            # append (default)
python3 scripts/add_songs.py "My Playlist Name" songs.txt --replace  # wipe + rebuild
```

Default **appends**: playlist created if missing, tracks already present are
skipped. `--replace` wipes and rebuilds. Output lists resolved catalog matches,
add-to-library status, and an ADDED / ALREADY PRESENT / MISSING report.

## How it works

- **Catalog search**: iTunes Search API — free, no auth — resolves each
  `Artist - Title` to a `trackId`.
- **Dev token**: fetched from the hosted `/devtoken` endpoint (cached in
  `dev_token.json` until near expiry). The MusicKit `.p8` lives only on that server.
- **Add to library**: `POST /v1/me/library?ids[songs]=...` with the dev token +
  your Music-User-Token.
- **Sweep**: AppleScript adds the matched library tracks into the playlist
  (append, dedup-aware).

## Files

- `config.json` — server_url + storefront
- `user_token.txt` — your Music User Token (gitignored)
- `dev_token.json` — cached dev token (gitignored)
- `scripts/get_token.py` — open the authorize page
- `scripts/add_songs.py` — main entry
- `scripts/common.py` — helpers

## Gotchas

- AppleScript reaches only library tracks — that's why the API add comes first.
- macOS + Music.app signed into the same Apple Music account required.
- python.org Python may lack CA certs → `certifi` provides them (used automatically).
