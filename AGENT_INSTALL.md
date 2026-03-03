# Memory Web UI — Agent Installation Guide

> This document is optimized for AI agents. For human-readable docs, see [README.md](README.md).

## Prompt Templates (Send to Your AI Agent)

**Simple — copy and send:**

```
Install Memory Web UI on my VPS.
Docs: https://github.com/YIING99/openclaw-memory-ui/blob/main/AGENT_INSTALL.md
Manifest: https://raw.githubusercontent.com/YIING99/openclaw-memory-ui/main/memory-ui.json
Password: SET_YOUR_PASSWORD
Language: zh
```

**With custom memory directory:**

```
Install Memory Web UI on my VPS.
Docs: https://github.com/YIING99/openclaw-memory-ui/blob/main/AGENT_INSTALL.md
Manifest: https://raw.githubusercontent.com/YIING99/openclaw-memory-ui/main/memory-ui.json
Password: SET_YOUR_PASSWORD
Language: zh
Memory directory: ~/my-knowledge-base
If Nginx is available, configure /memory/ sub-path.
```

---

## What This Is

Memory Web UI is a web interface for managing markdown (.md) knowledge base files. It provides browse, search, edit, folder management, and optional review workflow with a dark-themed responsive UI.

## Prerequisites

- Linux VPS (Ubuntu 20.04+)
- Python 3.8+
- Git
- Nginx (for reverse proxy, optional)
- systemd (for service management, optional)

Check prerequisites:
```bash
python3 --version && git --version && nginx -v 2>&1 && echo "ALL OK"
```

## Quick Install (One Command)

The installer accepts all configuration via CLI flags. No interactive prompts.

### Minimal install (English, defaults):
```bash
bash <(curl -sSL https://raw.githubusercontent.com/YIING99/openclaw-memory-ui/main/quick-install.sh) \
  --password "SET_PASSWORD_HERE"
```

### Full install with Chinese locale:
```bash
bash <(curl -sSL https://raw.githubusercontent.com/YIING99/openclaw-memory-ui/main/quick-install.sh) \
  --password "SET_PASSWORD_HERE" \
  --install-dir "$HOME/memory-ui" \
  --memory-dir "$HOME/memory" \
  --language zh \
  --port 5000 \
  --app-title "Memory UI" \
  --app-subtitle "知识记忆库" \
  --review-statuses "待审核,审核中,已通过,需修改,已发布" \
  --approved-statuses "已通过,已发布" \
  --drafts-folder "草稿箱" \
  --nginx-path "/memory" \
  --preset "ai-agent"
```

## Parameter Reference

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--password` | **YES** | — | Login password (will be hashed) |
| `--install-dir` | no | `~/memory-ui` | Where to clone the repository |
| `--memory-dir` | no | `~/memory` | Directory containing .md files |
| `--language` | no | `en` | UI language: `en` or `zh` |
| `--port` | no | `5000` | Gunicorn listen port |
| `--app-title` | no | `Memory UI` | Brand name in navbar |
| `--app-subtitle` | no | `Markdown Knowledge Base` | Subtitle in footer |
| `--enable-review` | no | `true` | Enable review workflow |
| `--review-statuses` | no | `pending,in_review,...` | Comma-separated status values |
| `--approved-statuses` | no | `approved,published` | Which statuses = approved |
| `--drafts-folder` | no | `drafts` | Folder name for drafts |
| `--reindex-cmd` | no | (empty=disabled) | Command to run after edits |
| `--reindex-timeout` | no | `120` | Timeout for reindex (seconds) |
| `--openclaw-home` | no | `~` | HOME env for reindex subprocess |
| `--nginx-path` | no | (empty) | Sub-path for nginx (e.g. `/memory`) |
| `--no-systemd` | no | — | Skip systemd service setup |
| `--preset` | no | (empty) | Template: `ai-agent`, `dev-notes`, or `personal` |

## Post-Install Verification

Run these commands to verify the installation succeeded:

```bash
# 1. Check service is running
systemctl --user is-active memory-ui
# Expected output: active

# 2. Check HTTP response
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:PORT/login
# Expected output: 200 (replace PORT with actual port)

# 3. Check logs if something is wrong
journalctl --user -u memory-ui -n 30 --no-pager
```

## Nginx Setup (If Using Reverse Proxy)

After installing, add this to your nginx `server {}` block:

```nginx
location /memory/ {
    proxy_pass http://127.0.0.1:PORT/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Script-Name /memory;
}
```

Replace `PORT` with the actual port number. Then:
```bash
nginx -t && systemctl reload nginx
```

Verify public access:
```bash
curl -s -o /dev/null -w "%{http_code}" http://YOUR_SERVER_IP/memory/login
# Expected: 200
```

## Upgrade

Re-run the install command with the same parameters. The script is idempotent:
- Pulls latest code via `git pull`
- Preserves existing `.env` secret key
- Backs up existing `.env` to `.env.bak`
- Restarts the systemd service

## Uninstall

```bash
systemctl --user stop memory-ui
systemctl --user disable memory-ui
rm ~/.config/systemd/user/memory-ui.service
systemctl --user daemon-reload
rm -rf ~/memory-ui  # or your --install-dir
# Note: memory files in --memory-dir are NOT deleted
```

## Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| Service won't start | `journalctl --user -u memory-ui -n 30` | Check .env syntax |
| Port already in use | `lsof -i :PORT` | Change `--port` or stop other service |
| 502 from nginx | `curl http://127.0.0.1:PORT/login` | Service not running, restart it |
| Login fails | Check password hash in `.env` | Re-run installer with correct `--password` |
| No files shown | `ls MEMORY_DIR/*.md` | Check `--memory-dir` path is correct |

## Important: Memory Directory

The default `--memory-dir` is `~/memory` — a fresh empty directory. **Do NOT auto-detect or reuse existing directories** unless the user explicitly provides a path. Each installation should have its own independent memory directory.

If the user wants to use an existing markdown directory, they must explicitly specify it via `--memory-dir /path/to/their/directory`.
