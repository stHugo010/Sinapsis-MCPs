import os
import sys

import re
from fastmcp import FastMCP, Context

VAULT_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Documents/Obsidian")

mcp = FastMCP("obsidian-busqueda")

@mcp.tool(tags={"search", "obsidian"}, annotations={"readOnlyHint": True}, timeout=15.0)
async def buscar_palabra(keyword: str, ctx: Context = None) -> list[str]:
    """Devuelve las notas que contienen una palabra clave."""
    await ctx.info(f"Buscando '{keyword}' en el vault...")
    all_files = [
        os.path.join(r, f)
        for r, _, files in os.walk(VAULT_PATH)
        for f in files if f.endswith(".md")
    ]
    encontradas = []
    for i, filepath in enumerate(all_files):
        await ctx.report_progress(progress=i, total=len(all_files))
        with open(filepath, "r", encoding="utf-8") as f:
            if keyword.lower() in f.read().lower():
                encontradas.append(os.path.basename(filepath).replace(".md", ""))
    await ctx.info(f"Encontradas {len(encontradas)} notas")
    return encontradas

@mcp.tool(tags={"search", "obsidian"}, annotations={"readOnlyHint": True}, timeout=15.0)
async def buscar_backlinks(nombre_nota: str, ctx: Context = None) -> list[str]:
    """Encuentra todas las notas que enlazan a la nota especificada."""
    await ctx.info(f"Buscando backlinks de: {nombre_nota}")
    pattern = re.compile(r"\[\[" + re.escape(nombre_nota) + r"([\|#\]])", re.IGNORECASE)
    all_files = [
        os.path.join(r, f)
        for r, _, files in os.walk(VAULT_PATH)
        for f in files if f.endswith(".md")
    ]
    enlaces = []
    for i, filepath in enumerate(all_files):
        await ctx.report_progress(progress=i, total=len(all_files))
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                if pattern.search(f.read()):
                    enlaces.append(os.path.basename(filepath).replace(".md", ""))
        except Exception:
            continue
    await ctx.info(f"Encontrados {len(enlaces)} backlinks")
    return enlaces