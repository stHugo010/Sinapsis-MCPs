"""
Herramientas de personalización para Google Calendar MCP

Este módulo contiene las tools para gestionar colores, recordatorios
y personalización de eventos.
"""

from fastmcp import Context
from helpers import get_service, get_color_id, get_color_name


def register_personalizacion_tools(mcp):
    """
    Registra todas las tools de personalización en el servidor MCP.
    
    Args:
        mcp: Instancia de FastMCP
    """
    
    @mcp.tool()
    async def set_event_color(
        event_id: str,
        color: str,
        calendar_id: str = "primary",
        ctx: Context = None
    ) -> dict:
        """
        Establece el color de un evento.
        
        Colores disponibles:
        - lavender, sage, grape, flamingo, banana
        - tangerine, peacock, graphite, blueberry, basil, tomato
        
        Args:
            event_id: ID del evento
            color: Nombre del color
            calendar_id: ID del calendario (default: "primary")
            
        Returns:
            Confirmación con event_id y color aplicado
            
        Example:
            >>> await set_event_color("abc123", "tomato")
            {"event_id": "abc123", "color": "tomato", "color_id": "11"}
        """
        await ctx.info(f"Estableciendo color {color} al evento {event_id}")
        
        service = get_service()
        
        color_id = get_color_id(color)
        
        if not color_id:
            return {
                "error": f"Color '{color}' no válido",
                "available_colors": list(get_color_id.__globals__['CALENDAR_COLORS'].keys())
            }
        
        # Obtener evento y actualizar color
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        event["colorId"] = color_id
        
        result = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()
        
        await ctx.info(f"Color actualizado correctamente")
        
        return {
            "event_id": event_id,
            "color": color,
            "color_id": color_id
        }
    
    
    @mcp.tool()
    async def add_reminder(
        event_id: str,
        minutes_before: int,
        method: str = "popup",
        calendar_id: str = "primary",
        ctx: Context = None
    ) -> dict:
        """
        Añade un recordatorio a un evento.
        
        Args:
            event_id: ID del evento
            minutes_before: Minutos antes del evento para el recordatorio
            method: Método de recordatorio: "popup" o "email" (default: "popup")
            calendar_id: ID del calendario (default: "primary")
            
        Returns:
            Confirmación con recordatorio añadido
            
        Example:
            >>> await add_reminder("abc123", 30, "popup")
            {"event_id": "abc123", "reminder": {"method": "popup", "minutes": 30}}
        """
        await ctx.info(f"Añadiendo recordatorio al evento {event_id}")
        
        service = get_service()
        
        # Obtener evento actual
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        # Añadir recordatorio
        if "reminders" not in event:
            event["reminders"] = {"useDefault": False, "overrides": []}
        
        if event["reminders"].get("useDefault"):
            event["reminders"]["useDefault"] = False
            event["reminders"]["overrides"] = []
        
        event["reminders"]["overrides"].append({
            "method": method,
            "minutes": minutes_before
        })
        
        result = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()
        
        await ctx.info("Recordatorio añadido correctamente")
        
        return {
            "event_id": event_id,
            "reminder": {
                "method": method,
                "minutes": minutes_before
            }
        }
    
    
    @mcp.tool()
    async def list_colors(ctx: Context = None) -> dict:
        """
        Lista todos los colores disponibles para eventos.
        
        Returns:
            Diccionario con nombres y IDs de colores
            
        Example:
            >>> await list_colors()
            {
                "lavender": "1",
                "sage": "2",
                ...
            }
        """
        await ctx.info("Listando colores disponibles")
        
        from helpers import CALENDAR_COLORS
        
        return CALENDAR_COLORS