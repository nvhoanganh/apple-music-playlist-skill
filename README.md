# 🎵 Apple Music Playlist Skill

A [Claude Code](https://claude.com/claude-code) skill that builds **Apple Music
playlists** on macOS from a plain `Artist - Title` list — including songs **not yet
in your library** (added via the Apple Music API, then swept into the playlist in
Music.app).

**No Apple Developer account required.** A hosted server supplies the developer
token — you bring only your **Apple Music subscription**.

---

## ✅ Requirements

- macOS with **Music.app** signed into your Apple Music account
- **Apple Music subscription**
- Python 3
- [Claude Code](https://claude.com/claude-code) (optional, but the skill auto-triggers there)

## ⚡ Install (one click)

```bash
curl -fsSL https://raw.githubusercontent.com/nvhoanganh/apple-music-playlist-skill/main/install.sh | bash
```

Installs into `~/.claude/skills/applemusic-playlist` and installs `certifi`.

<details>
<summary>Manual install</summary>

```bash
git clone https://github.com/nvhoanganh/apple-music-playlist-skill.git \
  ~/.claude/skills/applemusic-playlist
python3 -m pip install --user certifi
```
</details>

## 🚀 Usage

**1. Set your country** in `config.json`:
```json
{ "server_url": "https://applemusicplaylist.onrender.com", "storefront": "au" }
```

**2. Get your Music User Token** (once per ~6 months):
```bash
cd ~/.claude/skills/applemusic-playlist
python3 scripts/get_token.py
```
Opens the [authorize page](https://applemusicplaylist.onrender.com/authorize).
Sign in → token is shown and auto-copied → paste into `user_token.txt`.

**3. Add songs.** Make `songs.txt`, one `Artist - Title` per line:
```
Dire Straits - Iron Hand
Neil Young - Heart of Gold
John Mayer - Slow Dancing in a Burning Room (Acoustic)
```
Then:
```bash
python3 scripts/add_songs.py "My Playlist" songs.txt            # append (default)
python3 scripts/add_songs.py "My Playlist" songs.txt --replace  # wipe + rebuild
```

Or, in Claude Code, just say:
> add these to my Apple Music playlist "Road Trip": Fleetwood Mac - Landslide, ...

## 🔧 How it works

```
iTunes Search API ──> resolve trackIds (no auth)
authorize page    ──> your Music User Token (your account)
hosted /devtoken  ──> developer token (server's MusicKit .p8, never exposed)
       └── dev token + user token ──> POST /v1/me/library ──> your library
                                    ──> AppleScript sweep ──> playlist in Music.app
```

## 🔒 Privacy & security

- Your **Music User Token** stays on your machine (`user_token.txt`, gitignored).
  It grants library access to your Apple Music account; treat it like a password.
- The hosted server only mints a short-lived **developer token**; it never sees or
  stores your user token or library.
- Runs entirely locally otherwise — song adds and playlist edits happen on your Mac.

## 📝 Notes

- The hosted server is on a free tier; the first request after idle may take
  ~30–60s to wake.
- macOS only (uses AppleScript to control Music.app).

## License

MIT — see [LICENSE](LICENSE).
