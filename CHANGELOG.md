# Changelog

## v1.2.0 — 2026-03-03

### i18n & Generalization

Transform from OpenClaw-specific tool to a generic markdown knowledge base UI.

**New Features:**

- **i18n Support** — Full English and Chinese localization via JSON locale files (`locales/en.json`, `locales/zh.json`). Set `LANGUAGE=en` or `LANGUAGE=zh` in `.env`. Add your own language by creating a new locale file.
- **Setup Wizard** — Interactive `python setup.py` to configure language, password, memory directory, template pack, and branding in 30 seconds.
- **Template Packs** — Three pre-built `categories.json` templates in `presets/`:
  - `ai-agent` — AI agent knowledge base (Conversations/Knowledge/Learnings)
  - `dev-notes` — Developer notes (Projects/TIL/References)
  - `personal` — Personal knowledge base (Notes/Resources)
- **Configurable Review Statuses** — `REVIEW_STATUSES` and `APPROVED_STATUSES` env vars let you define your own review workflow labels (they're stored in frontmatter, so they're language-independent).
- **Configurable Drafts Folder** — `DRAFTS_FOLDER` env var (default: `drafts`).

**Breaking Changes (Migration Required):**

- Default `MEMORY_DIR` changed from `~/.openclaw/workspace/memory` to `~/memory`
- Default `REINDEX_COMMAND` changed from `npx openclaw memory index --force` to empty (disabled)
- Default `OPENCLAW_DIR` changed from `~/.openclaw` to empty
- Default `APP_SUBTITLE` changed from `OpenClaw Knowledge Base` to `Markdown Knowledge Base`
- Default `REVIEW_STATUSES` changed from Chinese to English (`pending,in_review,approved,needs_revision,published`)

**Migration for existing Chinese deployments:** Add to `.env`:
```
LANGUAGE=zh
REVIEW_STATUSES=待审核,审核中,已通过,需修改,已发布
APPROVED_STATUSES=已通过,已发布
DRAFTS_FOLDER=草稿箱
```

**Other Changes:**

- `categories.json` removed from git tracking (now instance-specific, won't be overwritten by `git pull`)
- All Python flash messages use i18n
- All HTML templates use `{{ t("key") }}` for UI strings
- README rewritten from generic perspective
- `.env.example` updated with all new variables

---

## v1.1.0 — 2026-03-03

### Folder Management

Organize your knowledge base with physical folders for better structure and discoverability.

**New Features:**

- **Folder Cards on Homepage** — Homepage now displays folder cards with file counts, replacing the old category overview. Click any folder to browse its contents.
- **Create Folder** — Create new folders directly from the homepage via a modal dialog.
- **Rename Folder** — Rename any folder from the browse view. File paths in `_index.json` are automatically updated.
- **Delete Folder** — Delete a folder; files inside are automatically moved to a configurable "drafts" folder instead of being lost.
- **Move File** — Move any file to a different folder from the detail view page ("Move to..." button).
- **Batch Move** — Select multiple files with checkboxes in the browse view and move them to a target folder in one action.
- **Folder Selector on New File** — When creating a new file, choose which folder to save it to (defaults to drafts folder).
- **Root Files Section** — Homepage shows uncategorized files (in root directory) separately, making it easy to spot files that need organizing.

**Bug Fixes:**

- **Fix login redirect under reverse proxy** — When session expires and user re-logs in, the redirect now correctly includes the `SCRIPT_NAME` prefix (e.g. `/memory/`). Previously, it would redirect to `/` and show the Nginx welcome page instead of the app. ([#1](https://github.com/YIING99/openclaw-memory-ui/commit/2f56e65))
- **Fix JSON serialization of date fields** — `python-frontmatter` parses YAML dates as `datetime.date` objects. Added `default=str` fallback to `json.dump()` to prevent index rebuild failures.

**UI Improvements:**

- Modal dialogs for create/rename folder and move file (dark-themed, click-outside-to-close)
- Batch action bar appears when files are selected (shows count + folder picker + move button)
- Folder tags shown in the "Recent Updates" list so you can see which folder each file belongs to
- Section headers with inline action buttons

**Architecture Notes:**

- Folders are physical subdirectories under `memory/`. Index tools can recursively index all subdirectories, so search works across all folders with no additional configuration.
- The `_index.json` stores relative paths (e.g. `folder/DOC-001.md`), updated automatically on move/rename operations.
- `all_folders` is injected into all templates via Flask `context_processor` for consistent folder access.

---

## v1.0.0 — 2026-02-28

Initial release.

- Browse & search memory files
- Markdown rendering with syntax highlighting
- YAML frontmatter editing via form UI
- Optional review workflow (approve/reject)
- Customizable categories via `categories.json`
- Auto re-index after edits
- Dark theme, responsive design
- Password authentication
- Nginx reverse proxy support
- Configurable re-index command
