#!/bin/bash
# OpenClaw Memory Web UI — Deployment Script
# Usage: bash deploy.sh
set -e

echo "=== OpenClaw Memory Web UI Deployment ==="
echo ""

# Configuration
read -rp "Install directory [/opt/memory-ui]: " INSTALL_DIR
INSTALL_DIR="${INSTALL_DIR:-/opt/memory-ui}"

read -rp "Memory directory [~/.openclaw/workspace/memory]: " MEMORY_DIR
MEMORY_DIR="${MEMORY_DIR:-$HOME/.openclaw/workspace/memory}"

read -rp "OpenClaw directory [~/.openclaw]: " OPENCLAW_DIR
OPENCLAW_DIR="${OPENCLAW_DIR:-$HOME/.openclaw}"

read -rp "Bind address [127.0.0.1:5000]: " BIND_ADDR
BIND_ADDR="${BIND_ADDR:-127.0.0.1:5000}"

read -rsp "Set a password for the web UI: " UI_PASSWORD
echo ""

if [ -z "$UI_PASSWORD" ]; then
    echo "Error: Password cannot be empty"
    exit 1
fi

PASSWORD_HASH=$(python3 -c "import hashlib; print(hashlib.sha256('${UI_PASSWORD}'.encode()).hexdigest())")
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

echo ""
echo "--- Configuration Summary ---"
echo "Install dir:  $INSTALL_DIR"
echo "Memory dir:   $MEMORY_DIR"
echo "OpenClaw dir: $OPENCLAW_DIR"
echo "Bind address: $BIND_ADDR"
echo "-----------------------------"
echo ""
read -rp "Continue? [Y/n] " CONFIRM
if [[ "$CONFIRM" =~ ^[Nn] ]]; then
    echo "Aborted."
    exit 0
fi

# Create install directory
echo "Creating $INSTALL_DIR ..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r app.py config.py categories.json gunicorn.conf.py requirements.txt templates/ static/ "$INSTALL_DIR/"
sudo chown -R "$USER:$USER" "$INSTALL_DIR"

# Create virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install -q -r "$INSTALL_DIR/requirements.txt"

# Create .env file
cat > "$INSTALL_DIR/.env" << EOF
MEMORY_DIR=$MEMORY_DIR
OPENCLAW_DIR=$OPENCLAW_DIR
OPENCLAW_HOME=$HOME
MEMORY_UI_PASSWORD_HASH=$PASSWORD_HASH
MEMORY_UI_SECRET_KEY=$SECRET_KEY
BIND=$BIND_ADDR
WORKERS=2
ENABLE_REVIEW=true
APP_TITLE=Memory UI
APP_SUBTITLE=OpenClaw Knowledge Base
EOF

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "To start the server:"
echo "  cd $INSTALL_DIR"
echo "  source venv/bin/activate"
echo "  gunicorn -c gunicorn.conf.py app:app"
echo ""
echo "Or set up as a systemd service — see deploy/memory-ui.service"
echo ""
