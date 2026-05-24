"""
Herramientas de notificación para Telegram MCP

Este módulo contiene las tools para enviar notificaciones categorizadas
por fuente: Obsidian, Google Calendar, Notion y Sistema.
"""

from fastmcp import Context
from helpers import send_message, get_timestamp, log_notification


def register_notificaciones_tools(mcp, base_url: str, chat_id: str):
    """
    Registra todas las tools de notificación en el servidor MCP.
    
    Args:
        mcp: Instancia de FastMCP
        base_url: URL base de la API de Telegram
        chat_id: ID del chat destino
    """
    
    @mcp.tool()
    async def notify_obsidian(
        action: str,
        detail: str,
        reason: str,
        ctx: Context = None
    ) -> dict:
        """
        Notifica una acción sobre el vault de Obsidian.
        
        Args:
            action: Descripción corta de lo que se hizo (ej: 'Nota creada: daily/2026-03-28.md')
            detail: Detalle adicional opcional (ej: nombre de carpeta, etiquetas)
            reason: Por qué el agente ha realizado esta acción
            
        Returns:
            Respuesta JSON de la API de Telegram
        """
        await ctx.info(f"Notificando acción Obsidian: {action}")
        
        text = (
            f"🗂️ *VAULT OBSIDIAN*\n"
            f"─────────────────\n"
            f"📝 {action}\n"
            f"{f'📁 {detail}' if detail else ''}\n\n"
            f"💬 _{reason}_\n\n"
            f"🕐 {get_timestamp()}"
        )
        
        log_notification("obsidian", action, reason)
        return await send_message(base_url, chat_id, text)
    
    
    @mcp.tool()
    async def notify_calendar(
        action: str,
        event_name: str,
        datetime_range: str,
        reason: str,
        ctx: Context = None
    ) -> dict:
        """
        Notifica una acción sobre Google Calendar.
        
        Args:
            action: 'creado' | 'modificado' | 'eliminado'
            event_name: Nombre del evento
            datetime_range: Rango legible (ej: 'Mañana 10:00 → 11:00')
            reason: Por qué el agente ha realizado esta acción
            
        Returns:
            Respuesta JSON de la API de Telegram
        """
        icons = {"creado": "✅", "modificado": "✏️", "eliminado": "🗑️"}
        icon = icons.get(action.lower(), "📅")
        
        await ctx.info(f"Notificando acción Calendar: {action} - {event_name}")
        
        text = (
            f"📅 *GOOGLE CALENDAR*\n"
            f"─────────────────\n"
            f"{icon} Evento {action}: `{event_name}`\n"
            f"📆 {datetime_range}\n\n"
            f"💬 _{reason}_\n\n"
            f"🕐 {get_timestamp()}"
        )
        
        log_notification("calendar", f"{action}: {event_name}", reason)
        return await send_message(base_url, chat_id, text)
    
    
    @mcp.tool()
    async def notify_notion(
        action: str,
        detail: str,
        reason: str,
        ctx: Context = None
    ) -> dict:
        """
        Notifica una acción sobre Notion.
        
        Args:
            action: Descripción corta (ej: 'Tarea completada: Revisar capítulo 3')
            detail: Página o base de datos afectada
            reason: Por qué el agente ha realizado esta acción
            
        Returns:
            Respuesta JSON de la API de Telegram
        """
        await ctx.info(f"Notificando acción Notion: {action}")
        
        text = (
            f"📓 *NOTION*\n"
            f"─────────────────\n"
            f"✳️ {action}\n"
            f"{f'📄 {detail}' if detail else ''}\n\n"
            f"💬 _{reason}_\n\n"
            f"🕐 {get_timestamp()}"
        )
        
        log_notification("notion", action, reason)
        return await send_message(base_url, chat_id, text)
    
    
    @mcp.tool()
    async def notify_system(
        event: str,
        detail: str,
        level: str = "info",
        ctx: Context = None
    ) -> dict:
        """
        Notifica un evento del centinela del sistema.
        
        Args:
            event: Qué ha detectado el centinela (ej: 'CPU > 90% durante 5 min')
            detail: Contexto adicional
            level: 'info' | 'warning' | 'critical'
            
        Returns:
            Respuesta JSON de la API de Telegram
        """
        icons = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}
        icon = icons.get(level, "ℹ️")
        
        await ctx.info(f"Notificando evento sistema [{level}]: {event}")
        
        text = (
            f"{icon} *SISTEMA [{level.upper()}]*\n"
            f"─────────────────\n"
            f"🖥️ {event}\n"
            f"{f'🔍 {detail}' if detail else ''}\n\n"
            f"🕐 {get_timestamp()}"
        )
        
        log_notification("system", event, level)
        return await send_message(base_url, chat_id, text)