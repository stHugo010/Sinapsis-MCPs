import os
import sys

from datetime import datetime
from fastmcp import FastMCP, Context
from helpers import _find_note_path, _parse_frontmatter, _build_frontmatter
import shutil

VAULT_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Documents/Obsidian")
TEMPLATES_PATH = sys.argv[2] if len(sys.argv) > 2 else os.path.join(VAULT_PATH, "Templates")

mcp = FastMCP("obsidian-notas")

@mcp.tool(tags={"search", "obsidian"}, annotations={"readOnlyHint": True})
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

@mcp.tool(tags={"create", "obsidian"}, annotations={"readOnlyHint": True})
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
    - template_name: nombre de la plantilla sin extensión

    Las variables {{date}} y {{title}} se sustituyen automáticamente.
    Usa list_templates para ver las plantillas disponibles.
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

@mcp.tool(tags={"create", "obsidian"})
async def create_note(
    note_name: str,
    folder: str,
    content: str,
    ctx: Context = None
) -> str:
    """
    Crea una nota con contenido libre.
    - note_name: nombre de la nota sin extensión
    - folder: carpeta destino relativa al vault (ej: '_agent_context' o 'projects')
    - content: contenido completo de la nota (incluyendo frontmatter si se desea)
    """
    await ctx.info(f"Creando nota '{note_name}' en '{folder}'...")
    dest_dir = os.path.join(VAULT_PATH, folder)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, f"{note_name}.md")
    if os.path.exists(dest_path):
        return f"Error: Note '{note_name}' already exists at {dest_path}."
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(content)
    await ctx.info(f"Nota creada en: {dest_path}")
    return f"Note '{note_name}' created at {dest_path}."
    
@mcp.tool(tags={"delete", "obsidian"}, annotations={"destructiveHint": True})
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