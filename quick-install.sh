#!/bin/bash
# Memory Web UI — Non-Interactive Installer
# Designed for both human and AI agent use.
#
# Usage:
#   bash quick-install.sh --password "mypass" [options]
#
# Or via curl:
#   curl -sSL https://raw.githubusercontent.com/YIING99/openclaw-memory-ui/main/quick-install.sh \
#     | bash -s -- --password "mypass" [options]

set -euo pipefail

# ============================================================
# Defaults
# ============================================================
INSTALL_DIR=""
PASSWORD=""
MEMORY_DIR=""
LANGUAGE="en"
PORT="5000"
APP_TITLE="Memory UI"
APP_SUBTITLE="Markdown Knowledge Base"
ENABLE_REVIEW="true"
REVIEW_STATUSES=""
APPROVED_STATUSES=""
DRAFTS_FOLDER=""
REINDEX_CMD=""
REINDEX_TIMEOUT="120"
OPENCLAW_HOME=""
NGINX_PATH=""
SETUP_SYSTEMD="yes"
PRESET=""
REPO_URL="https://github.com/YIING99/openclaw-memory-ui.git"

# ============================================================
# Parse arguments
# ============================================================
usage() {
    cat <<'USAGE'
Memory Web UI Installer

Required:
  --password <pass>        Login password

Optional:
  --install-dir <path>     Installation directory (default: ~/memory-ui)
  --memory-dir <path>      Markdown files directory (default: ~/memory)
  --language <en|zh>       UI language (default: en)
  --port <port>            Gunicorn port (default: 5000)
  --app-title <title>      App title (default: Memory UI)
  --app-subtitle <sub>     App subtitle
  --enable-review <bool>   Enable review workflow (default: true)
  --review-statuses <csv>  Comma-separated review statuses
  --approved-statuses <csv> Comma-separated approved statuses
  --drafts-folder <name>   Drafts folder name
  --reindex-cmd <cmd>      Post-edit reindex command
  --reindex-timeout <sec>  Reindex timeout (default: 120)
  --openclaw-home <path>   HOME for reindex subprocess
  --nginx-path <path>      Nginx sub-path (e.g. /memory) — prints config
  --no-systemd             Skip systemd service setup
  --preset <name>          Template pack (ai-agent|dev-notes|personal)
  --help                   Show this help
USAGE
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --password)        PASSWORD="$2"; shift 2 ;;
        --install-dir)     INSTALL_DIR="$2"; shift 2 ;;
        --memory-dir)      MEMORY_DIR="$2"; shift 2 ;;
        --language)        LANGUAGE="$2"; shift 2 ;;
        --port)            PORT="$2"; shift 2 ;;
        --app-title)       APP_TITLE="$2"; shift 2 ;;
        --app-subtitle)    APP_SUBTITLE="$2"; shift 2 ;;
        --enable-review)   ENABLE_REVIEW="$2"; shift 2 ;;
        --review-statuses) REVIEW_STATUSES="$2"; shift 2 ;;
        --approved-statuses) APPROVED_STATUSES="$2"; shift 2 ;;
        --drafts-folder)   DRAFTS_FOLDER="$2"; shift 2 ;;
        --reindex-cmd)     REINDEX_CMD="$2"; shift 2 ;;
        --reindex-timeout) REINDEX_TIMEOUT="$2"; shift 2 ;;
        --openclaw-home)   OPENCLAW_HOME="$2"; shift 2 ;;
        --nginx-path)      NGINX_PATH="$2"; shift 2 ;;
        --no-systemd)      SETUP_SYSTEMD="no"; shift ;;
        --preset)          PRESET="$2"; shift 2 ;;
        --help)            usage ;;
        *) echo "ERROR: Unknown option: $1"; usage ;;
    esac
done

# ============================================================
# Validate
# ============================================================
if [[ -z "$PASSWORD" ]]; then
    echo "ERROR: --password is required"
    exit 1
fi

# Apply defaults
INSTALL_DIR="${INSTALL_DIR:-$HOME/memory-ui}"
MEMORY_DIR="${MEMORY_DIR:-$HOME/memory}"

echo "============================================"
echo "  Memory Web UI — Installing"
echo "============================================"
echo "Install dir:  $INSTALL_DIR"
echo "Memory dir:   $MEMORY_DIR"
echo "Language:      $LANGUAGE"
echo "Port:          $PORT"
echo "Systemd:       $SETUP_SYSTEMD"
echo "============================================"

# ============================================================
# Step 1: Clone or update repository
# ============================================================
echo ""
echo "[1/6] Repository..."
if [[ -d "$INSTALL_DIR/.git" ]]; then
    echo "  Existing installation found, pulling updates..."
    cd "$INSTALL_DIR"
    git pull --ff-only 2>/dev/null || git pull
    echo "  Updated."
else
    echo "  Cloning from $REPO_URL..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    echo "  Cloned."
fi

# ============================================================
# Step 2: Python virtual environment
# ============================================================
echo ""
echo "[2/6] Python environment..."
if [[ ! -d "$INSTALL_DIR/venv" ]]; then
    python3 -m venv "$INSTALL_DIR/venv"
    echo "  Created venv."
fi
"$INSTALL_DIR/venv/bin/pip" install -q --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -q -r "$INSTALL_DIR/requirements.txt"
echo "  Dependencies installed."

# ============================================================
# Step 3: Generate .env
# ============================================================
echo ""
echo "[3/6] Configuration..."
PW_HASH=$("$INSTALL_DIR/venv/bin/python3" -c "import hashlib; print(hashlib.sha256('${PASSWORD}'.encode()).hexdigest())")
SECRET_KEY=$("$INSTALL_DIR/venv/bin/python3" -c "import os; print(os.urandom(24).hex())")

# Preserve existing secret key if upgrading
if [[ -f "$INSTALL_DIR/.env" ]]; then
    EXISTING_SECRET=$(grep "^MEMORY_UI_SECRET_KEY=" "$INSTALL_DIR/.env" 2>/dev/null | cut -d'=' -f2-)
    if [[ -n "$EXISTING_SECRET" ]]; then
        SECRET_KEY="$EXISTING_SECRET"
    fi
    cp "$INSTALL_DIR/.env" "$INSTALL_DIR/.env.bak"
    echo "  Existing .env backed up to .env.bak"
fi

{
    echo "LANGUAGE=$LANGUAGE"
    echo "MEMORY_DIR=$MEMORY_DIR"
    echo "MEMORY_UI_PASSWORD_HASH=$PW_HASH"
    echo "MEMORY_UI_SECRET_KEY=$SECRET_KEY"
    echo "BIND=127.0.0.1:$PORT"
    echo "WORKERS=2"
    echo "APP_TITLE=$APP_TITLE"
    echo "APP_SUBTITLE=$APP_SUBTITLE"
    echo "ENABLE_REVIEW=$ENABLE_REVIEW"
    [[ -n "$REVIEW_STATUSES" ]] && echo "REVIEW_STATUSES=$REVIEW_STATUSES"
    [[ -n "$APPROVED_STATUSES" ]] && echo "APPROVED_STATUSES=$APPROVED_STATUSES"
    [[ -n "$DRAFTS_FOLDER" ]] && echo "DRAFTS_FOLDER=$DRAFTS_FOLDER"
    [[ -n "$REINDEX_CMD" ]] && echo "REINDEX_COMMAND=$REINDEX_CMD"
    echo "REINDEX_TIMEOUT=$REINDEX_TIMEOUT"
    [[ -n "$OPENCLAW_HOME" ]] && echo "OPENCLAW_HOME=$OPENCLAW_HOME"
} > "$INSTALL_DIR/.env"
echo "  .env written."

# ============================================================
# Step 4: Template pack
# ============================================================
echo ""
echo "[4/6] Template pack..."
if [[ -n "$PRESET" && -f "$INSTALL_DIR/presets/$PRESET/categories.json" ]]; then
    cp "$INSTALL_DIR/presets/$PRESET/categories.json" "$INSTALL_DIR/categories.json"
    echo "  Applied preset: $PRESET"
elif [[ -f "$INSTALL_DIR/categories.json" ]]; then
    echo "  Existing categories.json preserved."
else
    echo "  No preset selected, categories disabled."
fi

# Create memory directory
mkdir -p "$MEMORY_DIR"
echo "  Memory directory ready: $MEMORY_DIR"

# ============================================================
# Step 5: systemd service
# ============================================================
echo ""
echo "[5/6] Systemd service..."
if [[ "$SETUP_SYSTEMD" == "yes" ]]; then
    SERVICE_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SERVICE_DIR"

    cat > "$SERVICE_DIR/memory-ui.service" <<SYSTEMD_EOF
[Unit]
Description=Memory Web UI
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
SYSTEMD_EOF

    systemctl --user daemon-reload
    systemctl --user enable memory-ui 2>/dev/null || true
    systemctl --user restart memory-ui
    echo "  Service installed and started."

    # Enable linger so service runs without active login
    loginctl enable-linger "$(whoami)" 2>/dev/null || true
else
    echo "  Skipped (--no-systemd)."
fi

# ============================================================
# Step 6: Verify
# ============================================================
echo ""
echo "[6/6] Verification..."
sleep 2

if curl -s -o /dev/null -w "" "http://127.0.0.1:$PORT/login" 2>/dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/login")
    echo "  HTTP status: $HTTP_CODE"
    if [[ "$HTTP_CODE" == "200" ]]; then
        echo "  [OK] Memory Web UI is running!"
    else
        echo "  [WARN] Unexpected status code. Check: journalctl --user -u memory-ui -n 20"
    fi
else
    echo "  [WARN] Could not connect to port $PORT."
    echo "  Check: systemctl --user status memory-ui"
fi

# ============================================================
# Nginx hint
# ============================================================
if [[ -n "$NGINX_PATH" ]]; then
    echo ""
    echo "============================================"
    echo "  Nginx Configuration"
    echo "============================================"
    echo "Add this to your nginx server {} block:"
    echo ""
    echo "  location ${NGINX_PATH}/ {"
    echo "      proxy_pass http://127.0.0.1:${PORT}/;"
    echo "      proxy_set_header Host \$host;"
    echo "      proxy_set_header X-Real-IP \$remote_addr;"
    echo "      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;"
    echo "      proxy_set_header X-Forwarded-Proto \$scheme;"
    echo "      proxy_set_header X-Script-Name ${NGINX_PATH};"
    echo "  }"
    echo ""
    echo "Then: nginx -t && systemctl reload nginx"
fi

echo ""
echo "============================================"
echo "  Installation Complete!"
echo "============================================"
echo "  URL: http://127.0.0.1:$PORT"
[[ -n "$NGINX_PATH" ]] && echo "  Public: http://<your-ip>${NGINX_PATH}/"
echo "  Password: (the one you provided)"
echo ""
echo "  Manage:"
echo "    systemctl --user status memory-ui"
echo "    systemctl --user restart memory-ui"
echo "    journalctl --user -u memory-ui -f"
echo "============================================"
