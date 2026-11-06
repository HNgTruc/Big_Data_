"""PreToolUse hook: block creating or editing files directly in the project root.

Only the names in ALLOWED may live at the root. Everything else must be placed
in a folder. Exit code 2 blocks the tool call and sends stderr back to Claude.
Limitation: this guards Write/Edit/MultiEdit only, not files created through Bash.
"""
import json
import os
import sys

ALLOWED = {"README.md", ".gitignore"}


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    tool_input = data.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("path")
    if not path:
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    abs_path = os.path.abspath(path if os.path.isabs(path) else os.path.join(root, path))
    try:
        rel = os.path.relpath(abs_path, root)
    except ValueError:
        return 0
    if rel.startswith(".."):
        return 0
    parts = rel.replace("\\", "/").split("/")
    if len(parts) == 1 and parts[0] not in ALLOWED:
        sys.stderr.write(
            f"BLOCKED: '{parts[0]}' would sit directly in the project root. "
            "Only README.md and .gitignore are allowed there. "
            "Put the file in a suitable folder (see README.md for the folder map).\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
