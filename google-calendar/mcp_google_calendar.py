"""
Google Calendar MCP Server

Servidor MCP para gestionar Google Calendar.
Permite crear, modificar y eliminar eventos, buscar huecos libres,
gestionar múltiples calendarios, eventos recurrentes y personalización.
"""

from fastmcp import FastMCP
from tools.eventos import register_eventos_tools
from tools.busqueda import register_busqueda_tools
from tools.calendarios import register_calendarios_tools
from tools.recurrentes import register_recurrentes_tools
from tools.personalizacion import register_personalizacion_tools
from resources import register_resources
from prompts import register_prompts


def create_server() -> FastMCP:
    """
    Factory function para crear el servidor MCP de Google Calendar.
    
    Verifica que exista token.json y registra todas las herramientas,
    resources y prompts disponibles.
    
    Returns:
        Instancia configurada de FastMCP
        
    Raises:
        FileNotFoundError: Si token.json no existe
    """
    import os
    from helpers import TOKEN_PATH
    
    # Verificar que exista token.json
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(
            f"No se encontró {TOKEN_PATH}.\n"
            "Ejecuta 'python auth_setup.py' primero para generar el token."
        )
    
    # Crear instancia de FastMCP
    mcp = FastMCP(
        name="google-calendar",
        instructions=(
            "MCP para gestionar Google Calendar. "
            "Permite listar, crear, modificar y eliminar eventos, "
            "buscar huecos libres, gestionar múltiples calendarios, "
            "crear eventos recurrentes y personalizar con colores."
        )
    )
    
    # Registrar componentes
    register_eventos_tools(mcp)
    register_busqueda_tools(mcp)
    register_calendarios_tools(mcp)
    register_recurrentes_tools(mcp)
    register_personalizacion_tools(mcp)
    register_resources(mcp)
    register_prompts(mcp)
    
    return mcp