"""Search Apple Music catalog, add songs to library, sweep into a playlist.

Usage:
  python3 scripts/add_songs.py "Playlist Name" songs.txt            # append (default)
  python3 scripts/add_songs.py "Playlist Name" songs.txt --replace  # wipe + rebuild
  python3 scripts/add_songs.py "Playlist Name" - < songs.txt

songs.txt: one song per line, format  Artist - Title
Lines blank or starting with # are ignored.

Flow: iTunes Search API finds each track -> POST /me/library adds to iCloud
library -> poll until synced -> AppleScript sweeps matches into the playlist.
Default APPENDS (playlist created if missing, tracks already present skipped).
--replace wipes the playlist and rebuilds it from the given songs.
"""
import sys, json, time, subprocess, ssl, urllib.parse, urllib.request
from common import load_config, get_dev_token, get_user_token

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

API = "https://api.music.apple.com"


def parse_songs(path):
    text = sys.stdin.read() if path == "-" else open(path).read()
    songs = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if " - " not in line:
            print(f"  skip (no ' - '): {line}")
            continue
        artist, title = line.split(" - ", 1)
        songs.append((artist.strip(), title.strip()))
    return songs


def itunes_search(artist, title, storefront):
    term = urllib.parse.quote(f"{artist} {title}")
    url = (f"https://itunes.apple.com/search?term={term}"
           f"&entity=song&limit=5&country={storefront}")
    with urllib.request.urlopen(url, timeout=15, context=SSL_CTX) as r:
        data = json.load(r)
    results = data.get("results", [])
    if not results:
        return None
    # prefer a result whose artist matches; else first
    for res in results:
        if artist.lower() in res["artistName"].lower() or res["artistName"].lower() in artist.lower():
            return res
    return results[0]


def add_to_library(ids, dev, usr):
    q = urllib.parse.urlencode({"ids[songs]": ",".join(ids)}, safe="[],")
    req = urllib.request.Request(f"{API}/v1/me/library?{q}", method="POST")
    req.add_header("Authorization", f"Bearer {dev}")
    req.add_header("Music-User-Token", usr)
    req.add_header("Content-Length", "0")
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
        return r.status


def in_library(title, dev, usr):
    term = urllib.parse.quote(title)
    url = f"{API}/v1/me/library/search?term={term}&types=library-songs&limit=1"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {dev}")
    req.add_header("Music-User-Token", usr)
    try:
        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
            data = json.load(r)
        return bool(data.get("results", {}).get("library-songs", {}).get("data"))
    except Exception:
        return False


def applescript_sweep(playlist, matches, replace=False):
    """matches: list of (artist, title). Build+run an AppleScript sweep.

    Default appends to the playlist (created if missing), skipping tracks already
    present. replace=True wipes and rebuilds the playlist from `matches`.
    """
    def esc(s):
        return s.replace("\\", "\\\\").replace('"', '\\"')
    pairs = ", ".join('{"%s", "%s"}' % (esc(a), esc(t)) for a, t in matches)
    setup = (
        'if (exists playlist plName) then delete playlist plName\n'
        '    set pl to make new user playlist with properties {name:plName}'
        if replace else
        'if (exists playlist plName) then\n'
        '      set pl to playlist plName\n'
        '    else\n'
        '      set pl to make new user playlist with properties {name:plName}\n'
        '    end if'
    )
    script = f'''
on run
  set songList to {{{pairs}}}
  set plName to "{esc(playlist)}"
  tell application "Music"
    {setup}
    set added to {{}}
    set skipped to {{}}
    set missed to {{}}
    repeat with aSong in songList
      set theArtist to item 1 of aSong
      set theTitle to item 2 of aSong
      set didAdd to false
      set hits to (every track of library playlist 1 whose name contains theTitle)
      repeat with h in hits
        if (artist of h) contains theArtist or theArtist contains (artist of h) then
          set hname to (name of h)
          set hartist to (artist of h)
          set dupes to (every track of pl whose name is hname and artist is hartist)
          if (count of dupes) > 0 then
            set end of skipped to theArtist & " - " & theTitle
          else
            duplicate h to pl
            set end of added to theArtist & " - " & theTitle
          end if
          set didAdd to true
          exit repeat
        end if
      end repeat
      if not didAdd then set end of missed to theArtist & " - " & theTitle
    end repeat
  end tell
  set AppleScript's text item delimiters to linefeed
  return "ADDED (" & (count of added) & "):" & linefeed & (added as text) & ¬
    linefeed & linefeed & "ALREADY PRESENT (" & (count of skipped) & "):" & linefeed & (skipped as text) & ¬
    linefeed & linefeed & "MISSING (" & (count of missed) & "):" & linefeed & (missed as text)
end run
'''
    p = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else f"AppleScript error:\n{p.stderr}"


def main():
    argv = [a for a in sys.argv[1:] if a != "--replace"]
    replace = "--replace" in sys.argv
    if len(argv) < 2:
        raise SystemExit(
            "Usage: python3 scripts/add_songs.py \"Playlist Name\" songs.txt [--replace]\n"
            "Default appends (skips dupes); --replace wipes and rebuilds the playlist."
        )
    playlist, songfile = argv[0], argv[1]
    cfg = load_config()
    dev = get_dev_token(cfg)
    usr = get_user_token()
    songs = parse_songs(songfile)
    if not songs:
        raise SystemExit("No songs parsed.")

    print(f"Resolving {len(songs)} songs via catalog...")
    resolved, ids = [], []
    for artist, title in songs:
        res = itunes_search(artist, title, cfg["storefront"])
        if res:
            ids.append(str(res["trackId"]))
            resolved.append((res["artistName"], res["trackName"]))
            print(f"  OK  {artist} - {title}  =>  {res['artistName']} - {res['trackName']}")
        else:
            print(f"  MISS (not in catalog): {artist} - {title}")

    if ids:
        status = add_to_library(ids, dev, usr)
        print(f"add-to-library HTTP {status} ({len(ids)} songs)")
        # poll until the last one shows up (sync lag)
        print("Waiting for iCloud library sync...")
        for _ in range(10):
            time.sleep(3)
            if in_library(resolved[-1][1], dev, usr):
                break

    mode = "replace" if replace else "append"
    print(f"Sweeping into playlist '{playlist}' ({mode})...")
    out = applescript_sweep(playlist, songs, replace=replace)
    print(out)


if __name__ == "__main__":
    main()
