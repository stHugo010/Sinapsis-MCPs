from fastmcp import FastMCP, Context
import os
import sys
import re
import shutil
from collections import defaultdict
from datetime import datetime

VAULT_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Documents/Obsidian")
TEMPLATES_PATH = sys.argv[2] if len(sys.argv) > 2 else os.path.join(VAULT_PATH, "Templates")

mcp = FastMCP(
    name="Obsidian-URJC",
    instructions=f"""
    MCP para gestionar un vault de Obsidian.
    Vault en: {VAULT_PATH}
    Plantillas en: {TEMPLATES_PATH}

    Flujo recomendado para crear notas:
    1. Usa list_templates para ver las plantillas disponibles
    2. Usa create_note_from_template con la plantilla adecuada
    3. Usa update_frontmatter para ajustar metadatos si es necesario

    Para explorar el vault sin saturar el contexto, usa explore_folder en vez de get_vault_structure.
    """
)

# --- helpers ---

def _find_note_path(nombre: str) -> str | None:
    """Devuelve la ruta completa de una nota o None si no existe."""
    direct = os.path.join(VAULT_PATH, f"{nombre}.md")
    if os.path.exists(direct):
        return direct
    for root, dirs, files in os.walk(VAULT_PATH):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        if f"{nombre}.md" in files:
            return os.path.join(root, f"{nombre}.md")
    return None

def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Separa frontmatter y cuerpo. Devuelve ({}, contenido) si no hay frontmatter."""
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

# --- resources ---

@mcp.resource("obsidian://vault/structure")
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

@mcp.resource("obsidian://vault/tags")
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

@mcp.resource("obsidian://note/{nombre}")
def get_note_resource(nombre: str) -> str:
    """Contenido de una nota específica como resource."""
    path = _find_note_path(nombre)
    if not path:
        return f"Error: Note '{nombre}' not found."
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@mcp.resource("obsidian://templates")
def list_templates_resource() -> str:
    """Lista de plantillas disponibles en la carpeta Templates."""
    if not os.path.exists(TEMPLATES_PATH):
        return "Templates folder not found."
    templates = [f.replace(".md", "") for f in os.listdir(TEMPLATES_PATH) if f.endswith(".md")]
    return "\n".join(templates) if templates else "No templates found."

# --- tools: notas ---

@mcp.tool(tags={"search", "obsidian"})
async def find_note(nombre: str, ctx: Context = None) -> str:
    """Busca y devuelve el contenido de una nota por nombre."""
    await ctx.info(f"Buscando nota: {nombre}")
    path = _find_note_path(nombre)
    if not path:
        return f"Error: Note '{nombre}' not found in vault."
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    await ctx.info(f"Nota encontrada en: {path}")
    return content

@mcp.tool(tags={"create", "obsidian"})
async def list_templates(ctx: Context = None) -> list[str]:
    """Lista las plantillas disponibles en la carpeta Templates."""
    await ctx.info(f"Leyendo plantillas desde: {TEMPLATES_PATH}")
    if not os.path.exists(TEMPLATES_PATH):
        return []
    templates = [f.replace(".md", "") for f in os.listdir(TEMPLATES_PATH) if f.endswith(".md")]
    await ctx.info(f"Encontradas {len(templates)} plantillas")
    return templates

@mcp.tool(tags={"create", "obsidian"})
async def create_note_from_template(
    note_name: str,
    folder: str,
    template_name: str,
    ctx: Context = None
) -> str:
    """
    Crea una nota a partir de una plantilla.
    - note_name: nombre de la nota sin extensión
    - folder: carpeta destino relativa al vault (ej: 'Daily' o 'Proyectos/TFG')
    - template_name: nombre de la plantilla sin extensión (usa list_templates para ver las disponibles)

    Las variables {{date}} y {{title}} se sustituyen automáticamente.
    """
    await ctx.info(f"Creando nota '{note_name}' desde plantilla '{template_name}'...")

    template_path = os.path.join(TEMPLATES_PATH, f"{template_name}.md")
    if not os.path.exists(template_path):
        return f"Error: Template '{template_name}' not found in {TEMPLATES_PATH}."

    dest_dir = os.path.join(VAULT_PATH, folder)
    os.makedirs(dest_dir, exist_ok=True)

    dest_path = os.path.join(dest_dir, f"{note_name}.md")
    if os.path.exists(dest_path):
        return f"Error: Note '{note_name}' already exists at {dest_path}."

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("{{date}}", datetime.now().strftime("%Y-%m-%d"))
    content = content.replace("{{title}}", note_name)

    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(content)

    await ctx.info(f"Nota creada en: {dest_path}")
    return f"Note '{note_name}' created at {dest_path} from template '{template_name}'."

@mcp.tool(tags={"delete", "obsidian"})
async def delete_note(note_name: str, ctx: Context = None) -> str:
    """Elimina una nota del vault buscándola por nombre."""
    await ctx.info(f"Eliminando nota: {note_name}")
    path = _find_note_path(note_name)
    if not path:
        return f"Error: Note '{note_name}' not found."
    os.remove(path)
    await ctx.info(f"Nota eliminada: {path}")
    return f"Note '{note_name}' deleted from {path}."

@mcp.tool(tags={"move", "obsidian"})
async def move_note(note_name: str, destination_folder: str, ctx: Context = None) -> str:
    """
    Mueve una nota a otra carpeta del vault.
    - note_name: nombre de la nota sin extensión
    - destination_folder: ruta relativa al vault (ej: 'Archivo' o 'Proyectos/TFG')
    """
    await ctx.info(f"Moviendo nota '{note_name}' a '{destination_folder}'...")
    src_path = _find_note_path(note_name)
    if not src_path:
        return f"Error: Note '{note_name}' not found."

    dest_dir = os.path.join(VAULT_PATH, destination_folder)
    os.makedirs(dest_dir, exist_ok=True)

    dest_path = os.path.join(dest_dir, f"{note_name}.md")
    if os.path.exists(dest_path):
        return f"Error: A note named '{note_name}' already exists in '{destination_folder}'."

    shutil.move(src_path, dest_path)
    await ctx.info(f"Nota movida a: {dest_path}")
    return f"Note '{note_name}' moved to {dest_path}."

@mcp.tool(tags={"edit", "obsidian"})
async def update_frontmatter(
    note_name: str,
    updates: dict,
    ctx: Context = None
) -> str:
    """
    Actualiza campos del frontmatter de una nota sin tocar el cuerpo.
    - note_name: nombre de la nota
    - updates: dict con los campos a actualizar (ej: {"tags": "[tfg, python]", "status": "done"})
    """
    await ctx.info(f"Actualizando frontmatter de: {note_name}")
    path = _find_note_path(note_name)
    if not path:
        return f"Error: Note '{note_name}' not found."

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    fm, body = _parse_frontmatter(content)
    fm.update(updates)

    new_content = _build_frontmatter(fm) + "\n" + body
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    await ctx.info(f"Frontmatter actualizado: {list(updates.keys())}")
    return f"Frontmatter of '{note_name}' updated: {list(updates.keys())}."

# --- tools: búsqueda ---

@mcp.tool(tags={"search", "obsidian"})
async def buscar_palabra(keyword: str, ctx: Context = None) -> list[str]:
    """Devuelve las notas que contienen una palabra clave."""
    await ctx.info(f"Buscando '{keyword}' en el vault...")
    encontradas = []
    for root, dirs, files in os.walk(VAULT_PATH):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith(".md"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    if keyword.lower() in f.read().lower():
                        encontradas.append(file.replace(".md", ""))
    await ctx.info(f"Encontradas {len(encontradas)} notas")
    return encontradas

@mcp.tool(tags={"search", "obsidian"})
async def buscar_backlinks(nombre_nota: str, ctx: Context = None) -> list[str]:
    """Encuentra todas las notas que enlazan a la nota especificada."""
    await ctx.info(f"Buscando backlinks de: {nombre_nota}")
    pattern = re.compile(r"\[\[" + re.escape(nombre_nota) + r"([\|#\]])", re.IGNORECASE)
    enlaces = []
    for root, dirs, files in os.walk(VAULT_PATH):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith(".md"):
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        if pattern.search(f.read()):
                            enlaces.append(file.replace(".md", ""))
                except Exception:
                    continue
    await ctx.info(f"Encontrados {len(enlaces)} backlinks")
    return enlaces

# --- tools: carpetas ---

@mcp.tool(tags={"folder", "obsidian"})
async def explore_folder(path: str = "", ctx: Context = None) -> str:
    """
    Explora el contenido de una carpeta del vault.
    Usa "" para la raíz. Más eficiente que get_vault_structure para vaults grandes.
    """
    await ctx.info(f"Explorando carpeta: '{path or 'root'}'")
    full_path = os.path.join(VAULT_PATH, path)
    if not os.path.exists(full_path):
        return f"Error: Folder '{path}' does not exist."
    items = os.listdir(full_path)
    folders = [f"{f}/" for f in items if os.path.isdir(os.path.join(full_path, f)) and not f.startswith('.')]
    notes = [f for f in items if f.endswith('.md')]
    output = f"### Contents of: {path if path else 'Root'}\n"
    output += "**Folders:**\n" + ("\n".join(folders) if folders else "None") + "\n\n"
    output += "**Notes:**\n" + ("\n".join(notes) if notes else "None")
    return output

@mcp.tool(tags={"create", "obsidian"})
async def create_folder(folder_name: str, ctx: Context = None) -> str:
    """Crea una carpeta en el vault."""
    await ctx.info(f"Creando carpeta: {folder_name}")
    path = os.path.join(VAULT_PATH, folder_name)
    if os.path.exists(path):
        return f"Error: Folder '{folder_name}' already exists."
    os.makedirs(path)
    await ctx.info(f"Carpeta creada: {path}")
    return f"Folder '{folder_name}' created at {path}."

# --- prompts ---

@mcp.prompt("nueva_nota_diaria")
def daily_note_prompt() -> str:
    """Instrucciones para crear la nota diaria."""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""
Crea la nota diaria de hoy ({today}):
1. Usa list_templates para ver las plantillas disponibles
2. Elige la plantilla más adecuada para notas diarias
3. Crea la nota con create_note_from_template en la carpeta 'Daily'
4. Notifica por Telegram con notify_obsidian explicando que se ha creado la nota del día
"""

@mcp.prompt("archivar_nota")
def archive_note_prompt(nota: str) -> str:
    """Instrucciones para archivar una nota correctamente."""
    return f"""
Archiva la nota '{nota}':
1. Usa find_note para leer su contenido actual
2. Usa update_frontmatter para añadir status: archived y archived_date: {datetime.now().strftime("%Y-%m-%d")}
3. Usa move_note para moverla a la carpeta 'Archivo'
4. Notifica por Telegram con notify_obsidian
"""

if __name__ == "__main__":
    mcp.run()