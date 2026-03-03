"""Memory Web UI — Configuration"""
import os
import json
import hashlib

# === Language & i18n ===
LANGUAGE = os.environ.get("LANGUAGE", "en")

_LOCALE_DIR = os.path.join(os.path.dirname(__file__), "locales")
_LOCALE_FILE = os.path.join(_LOCALE_DIR, f"{LANGUAGE}.json")
if os.path.exists(_LOCALE_FILE):
    with open(_LOCALE_FILE, encoding="utf-8") as _f:
        LOCALE = json.load(_f)
else:
    with open(os.path.join(_LOCALE_DIR, "en.json"), encoding="utf-8") as _f:
        LOCALE = json.load(_f)

# === Path Configuration ===
MEMORY_DIR = os.environ.get(
    "MEMORY_DIR",
    os.path.expanduser("~/memory")
)
OPENCLAW_DIR = os.environ.get("OPENCLAW_DIR", "")
OPENCLAW_HOME = os.environ.get(
    "OPENCLAW_HOME",
    os.path.expanduser("~")
)

# === Authentication ===
# Password hash (sha256). Default password: changeme
# Generate: python3 -c "import hashlib; print(hashlib.sha256('yourpassword'.encode()).hexdigest())"
PASSWORD_HASH = os.environ.get(
    "MEMORY_UI_PASSWORD_HASH",
    hashlib.sha256("changeme".encode()).hexdigest()
)
SECRET_KEY = os.environ.get(
    "MEMORY_UI_SECRET_KEY",
    "memory-ui-default-secret-change-me"
)
SESSION_LIFETIME_HOURS = int(os.environ.get("SESSION_LIFETIME_HOURS", "72"))

# === Index File ===
INDEX_FILE = os.path.join(MEMORY_DIR, "_index.json")

# === Review System ===
ENABLE_REVIEW = os.environ.get("ENABLE_REVIEW", "true").lower() == "true"

# Review statuses: configurable via env, comma-separated.
# These values are stored in .md frontmatter, so they are NOT locale-dependent.
_default_statuses = "pending,in_review,approved,needs_revision,published"
REVIEW_STATUSES = [s.strip() for s in os.environ.get("REVIEW_STATUSES", _default_statuses).split(",")]

_default_approved = "approved,published"
APPROVED_STATUSES = set(s.strip() for s in os.environ.get("APPROVED_STATUSES", _default_approved).split(","))

# === Drafts Folder ===
DRAFTS_FOLDER = os.environ.get("DRAFTS_FOLDER", "drafts")

# === Branding ===
APP_TITLE = os.environ.get("APP_TITLE", "Memory UI")
APP_SUBTITLE = os.environ.get("APP_SUBTITLE", "Markdown Knowledge Base")

# === Categories ===
# Load from categories.json if available, otherwise empty
_CATEGORIES_FILE = os.path.join(os.path.dirname(__file__), "categories.json")
if os.path.exists(_CATEGORIES_FILE):
    with open(_CATEGORIES_FILE, "r", encoding="utf-8") as _f:
        CATEGORIES = json.load(_f)
else:
    CATEGORIES = {}

# === Re-index Configuration ===
# Custom command to run after edits (e.g. rebuild search index).
# Set to empty string to disable (default).
# Example: "npx openclaw memory index --force"
# Example: "python3 /path/to/rebuild.py"
REINDEX_COMMAND = os.environ.get("REINDEX_COMMAND", "")
REINDEX_TIMEOUT = int(os.environ.get("REINDEX_TIMEOUT", "120"))
