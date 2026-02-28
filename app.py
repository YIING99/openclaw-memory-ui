#!/usr/bin/env python3
"""
OpenClaw Memory Web UI
Web interface for managing OpenClaw memory/ markdown files
"""

import json
import os
import re
import hashlib
import subprocess
import threading
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, send_from_directory
)
import frontmatter
import markdown

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=config.SESSION_LIFETIME_HOURS)


# Reverse proxy support for sub-path deployment (e.g. /memory/)
# Reads X-Script-Name header set by Nginx
class ReverseProxied:
    def __init__(self, wsgi_app):
        self.app = wsgi_app

    def __call__(self, environ, start_response):
        script_name = environ.get("HTTP_X_SCRIPT_NAME", "")
        if script_name:
            environ["SCRIPT_NAME"] = script_name
            path_info = environ.get("PATH_INFO", "")
            if path_info.startswith(script_name):
                environ["PATH_INFO"] = path_info[len(script_name):]
        return self.app(environ, start_response)


app.wsgi_app = ReverseProxied(app.wsgi_app)


# Inject config into template context
@app.context_processor
def inject_config():
    return dict(config=config)


# ============================================================
# Utilities
# ============================================================

def load_index():
    """Load _index.json, return empty index if not found"""
    if os.path.exists(config.INDEX_FILE):
        with open(config.INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": 1, "entries": {}}


def save_index(index_data):
    """Save _index.json"""
    with open(config.INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)


def rebuild_index_from_files():
    """Rebuild _index.json from filesystem"""
    index_data = {"version": 1, "entries": {}}
    memory_dir = config.MEMORY_DIR

    for root, dirs, files in os.walk(memory_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if not fname.endswith(".md") or fname.startswith("_"):
                continue
            filepath = os.path.join(root, fname)
            relpath = os.path.relpath(filepath, memory_dir)
            try:
                post = frontmatter.load(filepath)
                file_id = post.get("id", fname[:-3])
                index_data["entries"][file_id] = {
                    "path": relpath,
                    "title": post.get("title", fname[:-3]),
                    "source": post.get("source", ""),
                    "category": post.get("category", ""),
                    "subcategory": post.get("subcategory", ""),
                    "review_status": post.get("review_status", ""),
                    "modified": post.get("modified", ""),
                    "tags": post.get("tags", []),
                }
            except Exception:
                file_id = fname[:-3]
                index_data["entries"][file_id] = {
                    "path": relpath,
                    "title": extract_title_from_content(filepath),
                    "source": "",
                    "category": "",
                    "subcategory": "",
                    "review_status": "",
                    "modified": datetime.fromtimestamp(
                        os.path.getmtime(filepath)
                    ).strftime("%Y-%m-%d"),
                    "tags": [],
                }

    save_index(index_data)
    return index_data


def extract_title_from_content(filepath):
    """Extract title from a .md file without frontmatter"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("## "):
                    title = line.lstrip("#").strip()
                    title = re.sub(r"^\[[\d-]+\]\s*", "", title)
                    return title
                if line and not line.startswith("#"):
                    return line[:60]
    except Exception:
        pass
    return os.path.basename(filepath)[:-3]


def read_md_file(file_id):
    """Read a .md file, return (frontmatter_post, raw_content, filepath)"""
    index = load_index()
    entry = index.get("entries", {}).get(file_id)

    if entry:
        filepath = os.path.join(config.MEMORY_DIR, entry["path"])
    else:
        filepath = os.path.join(config.MEMORY_DIR, f"{file_id}.md")

    if not os.path.exists(filepath):
        return None, None, None

    try:
        post = frontmatter.load(filepath)
    except Exception:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()
        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                raw = parts[2].lstrip("\n")
        post = frontmatter.Post(raw)
        post["id"] = file_id
        post["title"] = extract_title_from_content(filepath)
    return post, post.content, filepath


def render_markdown(text):
    """Render Markdown text to HTML"""
    return markdown.markdown(
        text,
        extensions=["extra", "codehilite", "toc", "nl2br"],
    )


def trigger_reindex():
    """Trigger post-edit command (e.g. search index rebuild) in background thread"""
    if not config.REINDEX_COMMAND:
        return

    def _reindex():
        try:
            env = os.environ.copy()
            env["HOME"] = config.OPENCLAW_HOME
            subprocess.run(
                config.REINDEX_COMMAND,
                shell=True,
                cwd=config.MEMORY_DIR,
                env=env,
                capture_output=True,
                text=True,
                timeout=config.REINDEX_TIMEOUT,
            )
        except Exception:
            pass

    thread = threading.Thread(target=_reindex, daemon=True)
    thread.start()


def generate_next_id(prefix):
    """Generate next available ID, e.g. DOC-042"""
    index = load_index()
    max_num = 0
    pattern = re.compile(rf"^{prefix}-(\d+)$")
    for fid in index.get("entries", {}):
        m = pattern.match(fid)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"{prefix}-{max_num + 1:03d}"


def simple_search(query):
    """Simple full-text search (BM25-style keyword matching)"""
    query_lower = query.lower()
    terms = query_lower.split()
    results = []
    memory_dir = config.MEMORY_DIR

    for root, dirs, files in os.walk(memory_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if not fname.endswith(".md") or fname.startswith("_"):
                continue
            filepath = os.path.join(root, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                content_lower = content.lower()

                score = 0
                for term in terms:
                    count = content_lower.count(term)
                    if count > 0:
                        score += count

                if score > 0:
                    post = frontmatter.loads(content)
                    title = post.get("title", "")
                    if not title:
                        title = extract_title_from_content(filepath)

                    snippet = ""
                    idx = content_lower.find(terms[0])
                    if idx >= 0:
                        start = max(0, idx - 50)
                        end = min(len(content), idx + 150)
                        snippet = content[start:end].replace("\n", " ").strip()
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(content):
                            snippet = snippet + "..."

                    file_id = post.get("id", fname[:-3])
                    results.append({
                        "id": file_id,
                        "title": title,
                        "snippet": snippet,
                        "score": score,
                        "review_status": post.get("review_status", ""),
                        "modified": post.get("modified", ""),
                    })
            except Exception:
                continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:50]


# ============================================================
# Authentication
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        if pw_hash == config.PASSWORD_HASH:
            session.permanent = True
            session["logged_in"] = True
            next_url = request.args.get("next", "")
            return redirect(next_url or url_for("index_page"))
        flash("密码错误", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================================================
# Core Routes
# ============================================================

@app.route("/")
@login_required
def index_page():
    """Home: recent files + category overview"""
    index = load_index()
    entries = index.get("entries", {})

    recent = sorted(
        entries.items(),
        key=lambda x: x[1].get("modified", ""),
        reverse=True,
    )[:20]

    category_stats = {}
    review_stats = {}
    for status in config.REVIEW_STATUSES:
        review_stats[status] = 0
    review_stats["未设置"] = 0

    for fid, entry in entries.items():
        source = entry.get("source", "") or "未分类"
        cat = entry.get("category", "") or "未分类"
        key = f"{source}/{cat}" if source else cat
        category_stats[key] = category_stats.get(key, 0) + 1

        rs = entry.get("review_status", "")
        if rs in review_stats:
            review_stats[rs] += 1
        else:
            review_stats["未设置"] += 1

    return render_template(
        "browse.html",
        recent=recent,
        category_stats=category_stats,
        review_stats=review_stats,
        total=len(entries),
    )


@app.route("/browse/")
@app.route("/browse/<path:subpath>")
@login_required
def browse(subpath=""):
    """Browse by directory"""
    index = load_index()
    entries = index.get("entries", {})

    filtered = {}
    for fid, entry in entries.items():
        path = entry.get("path", "")
        if subpath:
            if path.startswith(subpath + "/") or path.startswith(subpath):
                filtered[fid] = entry
        else:
            filtered[fid] = entry

    subdirs = set()
    for fid, entry in filtered.items():
        path = entry.get("path", "")
        if subpath:
            rel = path[len(subpath):].lstrip("/")
        else:
            rel = path
        parts = rel.split("/")
        if len(parts) > 1:
            subdirs.add(parts[0])

    current_files = {}
    for fid, entry in filtered.items():
        path = entry.get("path", "")
        if subpath:
            rel = path[len(subpath):].lstrip("/")
        else:
            rel = path
        if "/" not in rel:
            current_files[fid] = entry

    return render_template(
        "browse_dir.html",
        subpath=subpath,
        subdirs=sorted(subdirs),
        files=sorted(current_files.items(), key=lambda x: x[1].get("modified", ""), reverse=True),
        total=len(filtered),
    )


@app.route("/view/<file_id>")
@login_required
def view(file_id):
    """View a .md file (Markdown rendered)"""
    post, content, filepath = read_md_file(file_id)
    if post is None:
        abort(404)

    html_content = render_markdown(content)
    metadata = dict(post.metadata)

    return render_template(
        "view.html",
        file_id=file_id,
        metadata=metadata,
        html_content=html_content,
        raw_content=content,
    )


@app.route("/edit/<file_id>", methods=["GET", "POST"])
@login_required
def edit(file_id):
    """Edit page"""
    if request.method == "POST":
        return _save_file(file_id)

    post, content, filepath = read_md_file(file_id)
    if post is None:
        abort(404)

    metadata = dict(post.metadata)
    return render_template(
        "edit.html",
        file_id=file_id,
        metadata=metadata,
        content=content,
        categories=config.CATEGORIES,
        review_statuses=config.REVIEW_STATUSES,
        is_new=False,
    )


def _save_file(file_id):
    """Save an edited file"""
    index = load_index()
    entry = index.get("entries", {}).get(file_id)

    title = request.form.get("title", "").strip()
    source = request.form.get("source", "").strip()
    category = request.form.get("category", "").strip()
    subcategory = request.form.get("subcategory", "").strip()
    tags_str = request.form.get("tags", "").strip()
    review_status = request.form.get("review_status", "").strip()
    content = request.form.get("content", "")

    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
    today = datetime.now().strftime("%Y-%m-%d")

    if entry:
        filepath = os.path.join(config.MEMORY_DIR, entry["path"])
    else:
        filepath = os.path.join(config.MEMORY_DIR, f"{file_id}.md")

    old_post = None
    if os.path.exists(filepath):
        old_post = frontmatter.load(filepath)

    post = frontmatter.Post(content)
    if old_post:
        for k, v in old_post.metadata.items():
            post[k] = v

    post["id"] = file_id
    post["title"] = title
    post["source"] = source
    post["category"] = category
    post["subcategory"] = subcategory
    post["tags"] = tags
    post["review_status"] = review_status
    post["modified"] = today
    if not post.get("created"):
        post["created"] = today
    post["version"] = post.get("version", 0) + 1

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    if "entries" not in index:
        index["entries"] = {}
    index["entries"][file_id] = {
        "path": os.path.relpath(filepath, config.MEMORY_DIR),
        "title": title,
        "source": source,
        "category": category,
        "subcategory": subcategory,
        "review_status": review_status,
        "modified": today,
        "tags": tags,
    }
    save_index(index)

    trigger_reindex()

    flash("保存成功，正在后台重建索引", "success")
    return redirect(url_for("view", file_id=file_id))


@app.route("/new", methods=["GET", "POST"])
@login_required
def new_file():
    """Create a new file"""
    if request.method == "POST":
        source = request.form.get("source", "").strip()
        prefix = "DOC"
        for src_name, src_config in config.CATEGORIES.items():
            if src_name == source:
                prefix = src_config["prefix"]
                break
        file_id = generate_next_id(prefix)
        return _save_file(file_id)

    return render_template(
        "edit.html",
        file_id="",
        metadata={},
        content="",
        categories=config.CATEGORIES,
        review_statuses=config.REVIEW_STATUSES,
        is_new=True,
    )


@app.route("/search")
@login_required
def search():
    """Full-text search"""
    query = request.args.get("q", "").strip()
    results = []
    if query:
        results = simple_search(query)
    return render_template("search.html", query=query, results=results)


@app.route("/review")
@login_required
def review_page():
    """Review queue"""
    if not config.ENABLE_REVIEW:
        abort(404)

    index = load_index()
    entries = index.get("entries", {})

    pending = []
    for fid, entry in entries.items():
        rs = entry.get("review_status", "")
        if rs and rs not in config.APPROVED_STATUSES and rs != "":
            pending.append((fid, entry))

    pending.sort(key=lambda x: x[1].get("modified", ""), reverse=True)
    return render_template("review.html", pending=pending)


@app.route("/review/<file_id>/approve", methods=["POST"])
@login_required
def approve(file_id):
    """Approve a file"""
    if not config.ENABLE_REVIEW:
        abort(404)
    return _update_review_status(file_id, config.REVIEW_STATUSES[-2] if len(config.REVIEW_STATUSES) >= 2 else "approved")


@app.route("/review/<file_id>/reject", methods=["POST"])
@login_required
def reject(file_id):
    """Reject a file"""
    if not config.ENABLE_REVIEW:
        abort(404)
    return _update_review_status(file_id, config.REVIEW_STATUSES[-1] if config.REVIEW_STATUSES else "rejected")


def _update_review_status(file_id, new_status):
    """Update review status"""
    post, content, filepath = read_md_file(file_id)
    if post is None:
        abort(404)

    post["review_status"] = new_status
    post["modified"] = datetime.now().strftime("%Y-%m-%d")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    index = load_index()
    if file_id in index.get("entries", {}):
        index["entries"][file_id]["review_status"] = new_status
        index["entries"][file_id]["modified"] = post["modified"]
        save_index(index)

    if new_status in config.APPROVED_STATUSES:
        trigger_reindex()

    flash(f"已将 {file_id} 标记为「{new_status}」", "success")
    return redirect(url_for("review_page"))


@app.route("/rebuild-index", methods=["POST"])
@login_required
def rebuild_index():
    """Manually rebuild index"""
    rebuild_index_from_files()
    trigger_reindex()
    flash("索引已重建，向量索引正在后台更新", "success")
    return redirect(url_for("index_page"))


@app.route("/delete/<file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    """Delete a file"""
    post, content, filepath = read_md_file(file_id)
    if post is None:
        abort(404)

    os.remove(filepath)

    index = load_index()
    if file_id in index.get("entries", {}):
        del index["entries"][file_id]
        save_index(index)

    trigger_reindex()
    flash(f"已删除 {file_id}", "success")
    return redirect(url_for("index_page"))


# ============================================================
# API
# ============================================================

@app.route("/api/categories")
def api_categories():
    """Return category hierarchy as JSON"""
    return config.CATEGORIES


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    if not os.path.exists(config.INDEX_FILE):
        print("Building index...")
        rebuild_index_from_files()
        print("Index built")

    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 5000)),
        debug=True,
    )
