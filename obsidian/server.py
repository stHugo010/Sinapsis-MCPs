import sys
import os

from fastmcp import FastMCP

from resources import mcp as resources_mcp
from prompts import mcp as prompts_mcp
from tools.notas import mcp as notas_mcp
from tools.busqueda import mcp as busqueda_mcp
from tools.carpetas import mcp as carpetas_mcp

VAULT_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Documents/Obsidian")
TEMPLATES_PATH = sys.argv[2] if len(sys.argv) > 2 else os.path.join(VAULT_PATH, "Templates")

mcp = FastMCP(
    name="Obsidian-URJC",
    instructions=f"""
    MCP para gestionar un vault de Obsidian.
    Vault: {VAULT_PATH} | Templates: {TEMPLATES_PATH}

    Workflows disponibles (usa los prompts):
    - crear_nota: crea una nota consultando reglas y estructura del vault
    - archivar_nota: archiva una nota correctamente
    - nota_diaria: crea la nota del día

    Para explorar el vault sin saturar el contexto usa explore_folder, no get_vault_structure.
    """
)

mcp.mount(resources_mcp)
mcp.mount(prompts_mcp)
mcp.mount(notas_mcp)
mcp.mount(busqueda_mcp)
mcp.mount(carpetas_mcp)

if __name__ == "__main__":
    mcp.run()