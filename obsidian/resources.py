import os
import sys
import re
import json
from collections import defaultdict
from fastmcp import FastMCP
from helpers import _find_note_path, _parse_frontmatter

VAULT_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Documents/Obsidian")
TEMPLATES_PATH = sys.argv[2] if len(sys.argv) > 2 else os.path.join(VAULT_PATH, "Templates")

mcp = FastMCP("obsidian-resources")

@mcp.resource("obsidian://vault/structure", mime_type="text/plain", tags={"vault"})
def get_vault_structure() -> str:
    """Árbol completo del vault (solo carpetas y .md)."""
    structure = []
    for root, dirs, files in os.walk(VAULT_PATH):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        level = root.replace(VAULT_PATH, '').count(os.sep)
        indent = ' ' * 4 * level
        structure.append(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            if f.endswith('.md'):
                structure.append(f"{sub_indent}{f}")
    return "\n".join(structure)

@mcp.resource("obsidian://vault/tags", mime_type="text/plain", tags={"vault"})
def get_all_tags() -> str:
    """Índice de tags y las notas que contiene cada uno."""
    tag_to_notes = defaultdict(list)
    for root, dirs, files in os.walk(VAULT_PATH):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if not file.endswith('.md'):
                continue
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, VAULT_PATH)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read(2048)
                fm, _ = _parse_frontmatter(content)
                raw_tags = fm.get("tags", "")
                if raw_tags.startswith('['):
                    items = raw_tags.strip('[]').split(',')
                    tags = [i.strip().strip('"').strip("'") for i in items]
                else:
                    items = re.findall(r'-\s+(.+)', raw_tags)
                    tags = [i.strip() for i in items]
                for tag in tags:
                    if tag:
                        tag_to_notes[tag].append(rel_path)
            except Exception:
                continue
    if not tag_to_notes:
        return "No tags found in the vault frontmatter."
    output = [f"Tag Index ({len(tag_to_notes)} unique):\n"]
    for tag, notes in sorted(tag_to_notes.items(), key=lambda x: (-len(x[1]), x[0])):
        display = notes[:20]
        suffix = f"... (+{len(notes)-20} more)" if len(notes) > 20 else ""
        output.append(f"#{tag} ({len(notes)}): {', '.join(display)}{suffix}")
    return "\n".join(output)

@mcp.resource("obsidian://note/{nombre}", mime_type="text/plain", tags={"vault"})
def get_note_resource(nombre: str) -> str:
    """Contenido de una nota específica como resource."""
    path = _find_note_path(nombre)
    if not path:
        return f"Error: Note '{nombre}' not found."
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@mcp.resource("obsidian://templates", mime_type="text/plain", tags={"vault"})
def list_templates_resource() -> str:
    """Lista de plantillas disponibles en la carpeta Templates."""
    if not os.path.exists(TEMPLATES_PATH):
        return "Templates folder not found."
    templates = [f.replace(".md", "") for f in os.listdir(TEMPLATES_PATH) if f.endswith(".md")]
    return "\n".join(templates) if templates else "No templates found."

@mcp.resource("obsidian://vault/rules", mime_type="text/plain", tags={"vault"})
def get_vault_rules() -> str:
    """Reglas del vault: qué va en cada carpeta y convenciones de nomenclatura."""
    return """
# Reglas del Vault

## Estructura de carpetas
- Daily/          → notas diarias con formato YYYY-MM-DD
- Proyectos/      → una subcarpeta por proyecto activo
- Recursos/       → artículos, papers, referencias externas
- Archivo/        → notas finalizadas o en desuso
- Templates/      → solo plantillas, nunca notas reales

## Nomenclatura
- Notas diarias:  YYYY-MM-DD
- Proyectos:      nombre-del-proyecto (kebab-case)
- Recursos:       titulo-del-recurso (kebab-case)

## Frontmatter obligatorio
- date:    fecha de creación (YYYY-MM-DD)
- tags:    al menos un tag
- status:  draft | active | done | archived

## Plantillas por tipo de nota
- nota diaria   → plantilla: daily
- proyecto      → plantilla: proyecto
- recurso       → plantilla: recurso
- reunión       → plantilla: reunion
"""