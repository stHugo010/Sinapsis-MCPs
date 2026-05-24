"""
server.py
Servidor MCP Notion - Refactorizado

Integración con Notion API para gestión de páginas y bases de datos.

Uso:
    python -m src.server          # Modo stdio
    python -m src.server --dev    # Modo debug
"""

import logging
from mcp.server.fastmcp import FastMCP

from .config import init_config
from .constants import MCP_INSTRUCTIONS, SEARCH_LIMIT_MIN, SEARCH_LIMIT_MAX, PAGE_SIZE_MIN, PAGE_SIZE_MAX
from .core import (
    search_notion,
    get_page_content,
    create_page,
    append_to_page,
    list_database_items,
    create_database_entry,
)
from .utils import format_json_response, format_error, clamp


# ─── Inicialización ──────────────────────────────────────────────────────────
config = init_config()
logger = config.setup_logging()

# Servidor MCP
mcp = FastMCP(config.server_name, instructions=MCP_INSTRUCTIONS)


# ─── TOOL 1: Search ──────────────────────────────────────────────────────────
@mcp.tool()
async def search_pages(
    query: str = "",
    filter_type: str = "",
    limit: int = 20,
) -> str:
    """
    Busca páginas y bases de datos en Notion.
    
    Args:
        query: Texto a buscar (vacío = todo)
        filter_type: "page" o "database" para filtrar
        limit: Número máximo de resultados (1-100)
    
    Returns:
        JSON con resultados de búsqueda
    """
    logger.info(f"Tool: search_pages(query='{query}', filter={filter_type})")
    
    limit = int(clamp(limit, SEARCH_LIMIT_MIN, SEARCH_LIMIT_MAX))
    filter_val = filter_type if filter_type in ["page", "database"] else None
    
    try:
        data = search_notion(query=query, filter_type=filter_val, limit=limit)
        return format_json_response(data)
    except Exception as e:
        logger.error(f"Error en search_pages: {e}", exc_info=True)
        return format_error(str(e))


# ─── TOOL 2: Get Page Content ───────────────────────────────────────────────
@mcp.tool()
async def get_page(page_id: str) -> str:
    """
    Obtiene el contenido completo de una página.
    
    Args:
        page_id: ID de la página de Notion
    
    Returns:
        JSON con metadatos y bloques de la página
    """
    logger.info(f"Tool: get_page(page_id={page_id})")
    
    try:
        data = get_page_content(page_id)
        return format_json_response(data)
    except Exception as e:
        logger.error(f"Error en get_page: {e}", exc_info=True)
        return format_error(str(e))


# ─── TOOL 3: Create Page ─────────────────────────────────────────────────────
@mcp.tool()
async def create_notion_page(
    parent_id: str,
    title: str,
    content: str = "",
) -> str:
    """
    Crea una nueva página en Notion.
    
    Args:
        parent_id: ID de la página padre
        title: Título de la página
        content: Contenido inicial (opcional)
    
    Returns:
        JSON con ID y URL de la página creada
    """
    logger.info(f"Tool: create_notion_page(title='{title}')")
    
    try:
        data = create_page(parent_id=parent_id, title=title, content=content)
        return format_json_response(data)
    except Exception as e:
        logger.error(f"Error en create_notion_page: {e}", exc_info=True)
        return format_error(str(e))


# ─── TOOL 4: Append to Page ──────────────────────────────────────────────────
@mcp.tool()
async def append_text(
    page_id: str,
    text: str,
    block_type: str = "paragraph",
) -> str:
    """
    Añade texto a una página existente.
    
    Args:
        page_id: ID de la página
        text: Texto a añadir
        block_type: Tipo de bloque (paragraph, heading_1, etc.)
    
    Returns:
        JSON con resultado de la operación
    """
    logger.info(f"Tool: append_text(page_id={page_id}, type={block_type})")
    
    try:
        data = append_to_page(page_id=page_id, text=text, block_type=block_type)
        return format_json_response(data)
    except Exception as e:
        logger.error(f"Error en append_text: {e}", exc_info=True)
        return format_error(str(e))


# ─── TOOL 5: List Database Items ─────────────────────────────────────────────
@mcp.tool()
async def list_database(
    database_id: str,
    page_size: int = 10,
) -> str:
    """
    Lista las entradas de una base de datos.
    
    Args:
        database_id: ID de la base de datos
        page_size: Número de resultados (1-100)
    
    Returns:
        JSON con entradas de la database
    """
    logger.info(f"Tool: list_database(database_id={database_id})")
    
    page_size = int(clamp(page_size, PAGE_SIZE_MIN, PAGE_SIZE_MAX))
    
    try:
        data = list_database_items(database_id=database_id, page_size=page_size)
        return format_json_response(data)
    except Exception as e:
        logger.error(f"Error en list_database: {e}", exc_info=True)
        return format_error(str(e))


# ─── TOOL 6: Create Database Entry ───────────────────────────────────────────
@mcp.tool()
async def create_entry(
    database_id: str,
    properties: dict,
) -> str:
    """
    Crea una nueva entrada en una base de datos.
    
    Args:
        database_id: ID de la base de datos
        properties: Propiedades de la entrada (formato JSON)
    
    Returns:
        JSON con ID y URL de la entrada creada
    """
    logger.info(f"Tool: create_entry(database_id={database_id})")
    
    try:
        data = create_database_entry(database_id=database_id, properties=properties)
        return format_json_response(data)
    except Exception as e:
        logger.error(f"Error en create_entry: {e}", exc_info=True)
        return format_error(str(e))


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Notion MCP Server arrancando...")
    mcp.run(transport=config.transport)