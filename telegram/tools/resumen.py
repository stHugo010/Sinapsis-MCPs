"""
Herramienta de resumen para Telegram MCP

Este módulo contiene la tool para enviar resúmenes formateados
con múltiples puntos.
"""

from fastmcp import Context
from helpers import send_message, get_timestamp


def register_resumen_tools(mcp, base_url: str, chat_id: str):
    """
    Registra la tool de resumen en el servidor MCP.
    
    Args:
        mcp: Instancia de FastMCP
        base_url: URL base de la API de Telegram
        chat_id: ID del chat destino
    """
    
    @mcp.tool()
    async def send_summary(
        title: str,
        items: list[str],
        ctx: Context = None
    ) -> dict:
        """
        Envía un resumen con varios puntos.
        
        Útil para resúmenes diarios o reportes agregados.
        
        Args:
            title: Título del resumen
            items: Lista de puntos a incluir en el resumen
            
        Returns:
            Respuesta JSON de la API de Telegram
            
        Example:
            >>> await send_summary(
            ...     "Resumen del día",
            ...     ["3 notas creadas", "2 eventos programados"]
            ... )
        """
        await ctx.info(f"Enviando resumen: {title}")
        
        # Formatear bullets
        bullets = "\n".join(f"  • {item}" for item in items)
        
        text = (
            f"📊 *{title.upper()}*\n"
            f"─────────────────\n"
            f"{bullets}\n\n"
            f"🕐 {get_timestamp()}"
        )
        
        return await send_message(base_url, chat_id, text)