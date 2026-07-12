"""Shared helpers: config load, dev-token fetch (from your server), user token.

The developer token is fetched from your hosted server's /devtoken endpoint — the
MusicKit .p8 lives only on that server, never here. Users need no Apple Developer
account, only an Apple Music subscription.
"""
import json, time, ssl, pathlib, urllib.request

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
CONFIG = SKILL_DIR / "config.json"
CONFIG_LOCAL = SKILL_DIR / "config.local.json"
DEV_CACHE = SKILL_DIR / "dev_token.json"
USER_TOKEN_FILE = SKILL_DIR / "user_token.txt"


def load_config():
    if not CONFIG.exists():
        raise SystemExit(f"Missing {CONFIG}.")
    cfg = json.loads(CONFIG.read_text())
    if CONFIG_LOCAL.exists():           # optional per-user overrides
        cfg.update(json.loads(CONFIG_LOCAL.read_text()))
    if "YOUR-APP" in cfg.get("server_url", ""):
        raise SystemExit(
            "Set server_url in config.json (or config.local.json) to your deployed "
            "dev-token server URL."
        )
    return cfg


def get_dev_token(cfg):
    """Fetch a dev token from {server_url}/devtoken, cached until near expiry."""
    if DEV_CACHE.exists():
        try:
            c = json.loads(DEV_CACHE.read_text())
            if c.get("exp", 0) - time.time() > 300:
                return c["token"]
        except Exception:
            pass
    url = cfg["server_url"].rstrip("/") + "/devtoken"
    with urllib.request.urlopen(url, timeout=15, context=SSL_CTX) as r:
        data = json.load(r)
    token = data["token"]
    exp = time.time() + int(data.get("expiresIn", 3600))
    DEV_CACHE.write_text(json.dumps({"token": token, "exp": exp}))
    return token


def get_user_storefront(cfg, dev, usr):
    """The user's real Apple Music country (e.g. 'au'), read from their account.
    Falls back to config storefront, then 'us'."""
    try:
        req = urllib.request.Request("https://api.music.apple.com/v1/me/storefront")
        req.add_header("Authorization", f"Bearer {dev}")
        req.add_header("Music-User-Token", usr)
        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
            data = json.load(r)
        return data["data"][0]["id"]
    except Exception:
        return cfg.get("storefront", "us")


def get_user_token():
    if not USER_TOKEN_FILE.exists():
        raise SystemExit(
            f"Missing {USER_TOKEN_FILE}. Run: python3 scripts/get_token.py, "
            "authorize in the browser, and paste the token into that file."
        )
    return USER_TOKEN_FILE.read_text().strip()
