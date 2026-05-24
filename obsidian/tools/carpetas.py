import os
import sys

from fastmcp import FastMCP, Context

VAULT_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Documents/Obsidian")

mcp = FastMCP("obsidian-carpetas")


@mcp.tool(tags={"folder", "obsidian"}, annotations={"readOnlyHint": True})
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