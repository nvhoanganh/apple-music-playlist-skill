#!/usr/bin/env bash
# One-click installer for the applemusic-playlist Claude skill.
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/nvhoanganh/apple-music-playlist-skill/main/install.sh | bash
set -euo pipefail

REPO="https://github.com/nvhoanganh/apple-music-playlist-skill.git"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/applemusic-playlist"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "This skill controls macOS Music.app — macOS only. Aborting." >&2
  exit 1
fi

mkdir -p "$(dirname "$DEST")"
if [[ -d "$DEST/.git" ]]; then
  echo "Updating existing install at $DEST"
  git -C "$DEST" pull --ff-only
else
  echo "Cloning skill into $DEST"
  git clone --depth 1 "$REPO" "$DEST"
fi

python3 -m pip install --user --quiet certifi >/dev/null 2>&1 || true

cat <<EOF

✅ Installed to: $DEST

Next steps:
  1) cd "$DEST"
  2) Set your country in config.json  ("storefront": "us" / "au" / "gb" ...)
  3) python3 scripts/get_token.py        # authorize, then paste token into user_token.txt
  4) echo "Neil Young - Heart of Gold" > songs.txt
     python3 scripts/add_songs.py "My Playlist" songs.txt

Or just tell Claude Code: "add these songs to my Apple Music playlist ...".
EOF
