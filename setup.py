#!/usr/bin/env python3
"""
Memory Web UI — Interactive Setup Wizard
Generates .env and categories.json for first-time setup.
Run: python setup.py
"""

import hashlib
import json
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PRESETS_DIR = os.path.join(SCRIPT_DIR, "presets")


def ask(prompt, default=""):
    """Prompt user for input with optional default."""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result or default
    return input(f"{prompt}: ").strip()


def choose(prompt, options):
    """Let user choose from a numbered list."""
    print(f"\n{prompt}")
    for i, (key, label) in enumerate(options, 1):
        print(f"  {i}. {label}")
    while True:
        choice = input(f"Choose [1-{len(options)}]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1][0]
        print("Invalid choice, try again.")


def discover_presets():
    """Find available preset template packs."""
    presets = []
    if os.path.isdir(PRESETS_DIR):
        for name in sorted(os.listdir(PRESETS_DIR)):
            cat_file = os.path.join(PRESETS_DIR, name, "categories.json")
            if os.path.isfile(cat_file):
                presets.append(name)
    return presets


def main():
    print("=" * 50)
    print("  Memory Web UI — Setup Wizard")
    print("=" * 50)

    # Step 1: Language
    lang = choose(
        "Step 1/5 — Language",
        [("en", "English"), ("zh", "Chinese (中文)")],
    )

    # Step 2: Password
    print("\nStep 2/5 — Password")
    while True:
        password = input("Set your login password: ").strip()
        if len(password) >= 4:
            break
        print("Password must be at least 4 characters.")
    pw_hash = hashlib.sha256(password.encode()).hexdigest()

    # Step 3: Memory directory
    print("\nStep 3/5 — Memory Directory")
    print("Where are your markdown files stored?")
    default_dir = os.path.expanduser("~/memory")
    memory_dir = ask("Path", default_dir)
    memory_dir = os.path.expanduser(memory_dir)

    # Step 4: Template pack
    presets = discover_presets()
    preset_choice = None
    if presets:
        options = [(p, p) for p in presets] + [("none", "No template (empty categories)")]
        preset_choice = choose("Step 4/5 — Template Pack", options)
        if preset_choice == "none":
            preset_choice = None

    # Step 5: Branding
    print("\nStep 5/5 — Branding")
    app_title = ask("App title", "Memory UI")
    app_subtitle = ask("Subtitle", "Markdown Knowledge Base")
    reindex_cmd = ask("Post-edit reindex command (leave empty to skip)", "")

    # Review settings
    review = choose(
        "Enable review system?",
        [("true", "Yes"), ("false", "No")],
    )

    # Generate .env
    env_path = os.path.join(SCRIPT_DIR, ".env")
    if os.path.exists(env_path):
        backup = env_path + ".bak"
        shutil.copy2(env_path, backup)
        print(f"\nExisting .env backed up to {backup}")

    env_lines = [
        f"LANGUAGE={lang}",
        f'MEMORY_UI_PASSWORD_HASH={pw_hash}',
        f'MEMORY_UI_SECRET_KEY={os.urandom(24).hex()}',
        f'MEMORY_DIR={memory_dir}',
        f'APP_TITLE={app_title}',
        f'APP_SUBTITLE={app_subtitle}',
        f'ENABLE_REVIEW={review}',
    ]
    if reindex_cmd:
        env_lines.append(f'REINDEX_COMMAND={reindex_cmd}')

    with open(env_path, "w") as f:
        f.write("\n".join(env_lines) + "\n")
    print(f"\n.env written to {env_path}")

    # Copy template pack
    if preset_choice:
        src = os.path.join(PRESETS_DIR, preset_choice, "categories.json")
        dst = os.path.join(SCRIPT_DIR, "categories.json")
        shutil.copy2(src, dst)
        print(f"categories.json copied from presets/{preset_choice}/")

    # Create memory directory if needed
    if not os.path.isdir(memory_dir):
        os.makedirs(memory_dir, exist_ok=True)
        print(f"Created memory directory: {memory_dir}")

    print("\n" + "=" * 50)
    print("  Setup complete!")
    print("=" * 50)
    print(f"\nTo start the app:")
    print(f"  pip install -r requirements.txt")
    print(f"  python app.py")
    print(f"\nOr with gunicorn:")
    print(f"  gunicorn -c gunicorn.conf.py app:app")


if __name__ == "__main__":
    main()
