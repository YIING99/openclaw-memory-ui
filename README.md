# OpenClaw Memory Web UI

A lightweight web interface for managing [OpenClaw](https://github.com/nicepkg/openclaw) memory files. Browse, search, edit, and organize your `.md` knowledge base with a clean dark-themed UI.

**[中文说明](#中文说明)**

## Screenshots

| Home | View | Edit |
|------|------|------|
| ![Home](screenshots/home.jpg) | ![View](screenshots/view.jpg) | ![Edit](screenshots/edit.jpg) |

| Search | New Record | Detail View |
|--------|------------|-------------|
| ![Search](screenshots/search.jpg) | ![New](screenshots/new.jpg) | ![Detail](screenshots/view-detail.jpg) |

---

## Features

- **Browse & Search** — Navigate memory files by directory or full-text keyword search
- **Markdown Rendering** — View files with syntax highlighting and table of contents
- **YAML Frontmatter** — Edit metadata (title, tags, category, review status) via form UI
- **Review Workflow** — Optional approve/reject pipeline for content quality control
- **Customizable Categories** — Define your own category hierarchy via `categories.json`
- **Auto Re-index** — Triggers `openclaw memory index` after edits for semantic search
- **Dark Theme** — Responsive design that works on desktop and mobile
- **Simple Auth** — Password-protected with configurable session lifetime
- **Nginx Ready** — Built-in reverse proxy support for sub-path deployment

## Quick Start

```bash
# 1. Clone
git clone https://github.com/YIING99/openclaw-memory-ui.git
cd openclaw-memory-ui

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python app.py
# Visit http://127.0.0.1:5000 (default password: changeme)
```

## Configuration

All settings are controlled via environment variables. Copy `.env.example` to `.env` and customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_DIR` | `~/.openclaw/workspace/memory` | Path to your memory/ directory |
| `OPENCLAW_DIR` | `~/.openclaw` | Path to OpenClaw installation |
| `OPENCLAW_HOME` | `~` | HOME for re-index subprocess |
| `MEMORY_UI_PASSWORD_HASH` | sha256("changeme") | SHA256 hash of your password |
| `MEMORY_UI_SECRET_KEY` | (default) | Flask session secret key |
| `SESSION_LIFETIME_HOURS` | `72` | Session expiry in hours |
| `APP_TITLE` | `Memory UI` | Brand name shown in navbar & login |
| `APP_SUBTITLE` | `OpenClaw Knowledge Base` | Subtitle shown in footer & login |
| `ENABLE_REVIEW` | `true` | Enable review workflow (`true`/`false`) |
| `PORT` | `5000` | Dev server port |
| `BIND` | `127.0.0.1:5000` | Gunicorn bind address |
| `WORKERS` | `2` | Gunicorn worker count |
| `REINDEX_TIMEOUT` | `120` | Re-index command timeout (seconds) |

### Generate Password Hash

```bash
python3 -c "import hashlib; print(hashlib.sha256('yourpassword'.encode()).hexdigest())"
```

## Custom Categories

Edit `categories.json` to define your own category hierarchy:

```json
{
  "Notes": {
    "prefix": "NOTE",
    "categories": ["Technical", "Research", "Ideas"],
    "subcategories": {
      "Technical": ["Backend", "Frontend", "DevOps"]
    }
  }
}
```

- **prefix** — ID prefix for new files (e.g. `NOTE-001`)
- **categories** — First-level categories under this source
- **subcategories** — Second-level categories (optional)

Set `categories.json` to `{}` (empty object) to disable the category system entirely — the edit form will show only title, tags, and content.

## Production Deployment

### With Gunicorn + Nginx

```bash
# Install
pip install -r requirements.txt

# Run with gunicorn
gunicorn -c gunicorn.conf.py app:app

# Or use the deploy script
bash deploy/deploy.sh
```

See `deploy/` directory for:
- `deploy.sh` — Interactive deployment script
- `memory-ui.service` — systemd service template
- `nginx.conf` — Nginx reverse proxy configuration

### systemd Service

```bash
cp deploy/memory-ui.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now memory-ui
```

## Architecture

```
┌──────────┐     ┌─────────┐     ┌──────────────┐
│  Nginx   │────▶│ Gunicorn│────▶│  Flask App   │
│ (proxy)  │     │ (WSGI)  │     │  (app.py)    │
└──────────┘     └─────────┘     └──────┬───────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
              ┌─────▼─────┐     ┌──────▼──────┐    ┌──────▼──────┐
              │ memory/   │     │ _index.json │    │  openclaw   │
              │ *.md files│     │ (file index)│    │ memory index│
              └───────────┘     └─────────────┘    └─────────────┘
```

- **memory/*.md** — Markdown files with YAML frontmatter (your knowledge base)
- **_index.json** — Auto-generated file index for fast browsing
- **openclaw memory index** — Triggered after edits to update semantic search vectors

## License

MIT License. See [LICENSE](LICENSE).

## Author

KING

---

## 中文说明

OpenClaw Memory Web UI 是一个轻量级的 Web 界面，用于管理 [OpenClaw](https://github.com/nicepkg/openclaw) 的 memory/ 知识库文件。

### 功能特性

- 浏览和搜索 memory/ 目录中的 .md 文件
- Markdown 渲染预览（支持代码高亮、目录）
- 通过表单编辑 YAML frontmatter 元数据
- 可选的审核工作流（通过/驳回）
- 自定义分类体系（`categories.json`）
- 编辑后自动触发 OpenClaw 向量索引重建
- 深色主题，响应式设计，移动端友好
- 简单密码认证

### 快速开始

```bash
git clone https://github.com/YIING99/openclaw-memory-ui.git
cd openclaw-memory-ui
pip install -r requirements.txt
python app.py
# 访问 http://127.0.0.1:5000（默认密码: changeme）
```

### 配置

复制 `.env.example` 为 `.env`，修改其中的环境变量即可自定义所有配置。详见上方英文配置表。
