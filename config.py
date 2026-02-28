"""OpenClaw Memory Web UI — Configuration"""
import os
import json
import hashlib

# === Path Configuration ===
# Default: OpenClaw standard memory directory
MEMORY_DIR = os.environ.get(
    "MEMORY_DIR",
    os.path.expanduser("~/.openclaw/workspace/memory")
)
OPENCLAW_DIR = os.environ.get(
    "OPENCLAW_DIR",
    os.path.expanduser("~/.openclaw")
)
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
REVIEW_STATUSES = ["待审核", "审核中", "已通过", "需修改", "已发布"]
APPROVED_STATUSES = {"已通过", "已发布"}

# === Branding ===
APP_TITLE = os.environ.get("APP_TITLE", "Memory UI")
APP_SUBTITLE = os.environ.get("APP_SUBTITLE", "OpenClaw Knowledge Base")

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
# Default: OpenClaw memory index. Set to empty string to disable.
# Example: "npx openclaw memory index --force"
# Example: "python3 /path/to/rebuild.py"
REINDEX_COMMAND = os.environ.get("REINDEX_COMMAND", "npx openclaw memory index --force")
REINDEX_TIMEOUT = int(os.environ.get("REINDEX_TIMEOUT", "120"))
