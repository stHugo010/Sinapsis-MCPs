"""
Telegram MCP Server

Servidor MCP para enviar notificaciones a Telegram.
Actúa como canal de salida de todos los demás MCPs del ecosistema Sinapsis.
"""

from fastmcp import FastMCP
from tools.notificaciones import register_notificaciones_tools
from tools.resumen import register_resumen_tools
from resources import register_resources
from prompts import register_prompts
import os
from dotenv import load_dotenv


def create_server() -> FastMCP:
    """
    Factory function para crear el servidor MCP de Telegram.
    
    Carga las credenciales desde variables de entorno y registra
    todas las herramientas, resources y prompts.
    
    Returns:
        Instancia configurada de FastMCP
        
    Raises:
        ValueError: Si faltan variables de entorno requeridas
    """
    # Cargar variables de entorno
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), './', '.env'))
    
    # Validar configuración
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        raise ValueError(
            "Faltan variables de entorno requeridas: TELEGRAM_TOKEN y TELEGRAM_CHAT_ID"
        )
    
    # Construir URL base de la API
    base_url = f"https://api.telegram.org/bot{token}"
    
    # Crear instancia de FastMCP
    mcp = FastMCP("telegram")
    
    # Registrar componentes
    register_notificaciones_tools(mcp, base_url, chat_id)
    register_resumen_tools(mcp, base_url, chat_id)
    register_resources(mcp)
    register_prompts(mcp)
    
    return mcp