"""Open the hosted authorize page to get your Music User Token.

Usage: python3 scripts/get_token.py
Sign in, the page shows your token (auto-copied). Paste it into user_token.txt
in the skill folder.
"""
import subprocess, urllib.parse
from common import load_config

cfg = load_config()
url = cfg["server_url"].rstrip("/") + "/authorize?" + urllib.parse.urlencode(
    {"storefront": cfg.get("storefront", "us")}
)
print(f"Opening {url}\nSign in, copy the token, paste it into user_token.txt")
subprocess.run(["open", url])
