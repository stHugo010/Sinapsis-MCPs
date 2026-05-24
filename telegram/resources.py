"""
Resources para Telegram MCP

Este módulo contiene los endpoints de solo lectura que exponen
el historial de notificaciones de la sesión.
"""

from helpers import get_notification_log, get_filtered_log


def register_resources(mcp):
    """
    Registra todos los resources del Telegram MCP.
    
    Args:
        mcp: Instancia de FastMCP
    """
    
    @mcp.resource("telegram://log")
    def get_log() -> list[dict]:
        """
        Historial de todas las notificaciones enviadas en esta sesión.
        
        Returns:
            Lista completa de notificaciones con metadata:
            - source: Fuente de la notificación
            - action: Acción realizada
            - reason: Razón de la acción
            - ts: Timestamp ISO 8601
        """
        return get_notification_log()
    
    
    @mcp.resource("telegram://log/{source}")
    def get_log_by_source(source: str) -> list[dict]:
        """
        Historial filtrado por fuente específica.
        
        Args:
            source: Fuente a filtrar (obsidian | calendar | notion | system)
            
        Returns:
            Lista de notificaciones de la fuente especificada
        """
        return get_filtered_log(source)