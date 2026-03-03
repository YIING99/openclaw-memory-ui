# Changelog

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

- Folders are physical subdirectories under `memory/`. OpenClaw's `memory index` recursively indexes all subdirectories, so search and semantic retrieval work across all folders with no additional configuration.
- The `_index.json` stores relative paths (e.g. `素材库/MAT-001.md`), updated automatically on move/rename operations.
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
