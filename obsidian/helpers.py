import os
import sys
import re

VAULT_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Documents/Obsidian")

def _find_note_path(nombre: str) -> str | None:
    direct = os.path.join(VAULT_PATH, f"{nombre}.md")
    if os.path.exists(direct):
        return direct
    for root, dirs, files in os.walk(VAULT_PATH):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        if f"{nombre}.md" in files:
            return os.path.join(root, f"{nombre}.md")
    return None

def _parse_frontmatter(content: str) -> tuple[dict, str]:
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)', content, re.DOTALL)
    if not match:
        return {}, content
    fm_raw, body = match.group(1), match.group(2)
    fm = {}
    for line in fm_raw.splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            fm[key.strip()] = val.strip()
    return fm, body

def _build_frontmatter(fm: dict) -> str:
    lines = ["---"]
    for k, v in fm.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"