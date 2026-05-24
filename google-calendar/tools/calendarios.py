"""
Herramientas de gestión de múltiples calendarios para Google Calendar MCP

Este módulo contiene las tools para listar y trabajar con múltiples calendarios.
"""

from fastmcp import Context
from helpers import get_service


def register_calendarios_tools(mcp):
    """
    Registra todas las tools de gestión de calendarios en el servidor MCP.
    
    Args:
        mcp: Instancia de FastMCP
    """
    
    @mcp.tool()
    async def list_calendars(ctx: Context = None) -> list[dict]:
        """
        Lista todos los calendarios accesibles por el usuario.
        
        Incluye calendario principal, calendarios propios y calendarios compartidos.
        
        Returns:
            Lista de calendarios con id, summary, description, primary, accessRole
            
        Example:
            >>> await list_calendars()
            [
                {"id": "primary", "summary": "Mi Calendario", "primary": True, ...},
                {"id": "abc@group.calendar.google.com", "summary": "Trabajo", ...}
            ]
        """
        await ctx.info("Listando calendarios...")
        
        service = get_service()
        
        result = service.calendarList().list().execute()
        calendars = result.get("items", [])
        
        formatted = []
        for cal in calendars:
            formatted.append({
                "id": cal.get("id"),
                "summary": cal.get("summary"),
                "description": cal.get("description", ""),
                "primary": cal.get("primary", False),
                "access_role": cal.get("accessRole"),
                "background_color": cal.get("backgroundColor"),
                "foreground_color": cal.get("foregroundColor")
            })
        
        await ctx.info(f"Encontrados {len(formatted)} calendarios")
        
        return formatted
    
    
    @mcp.tool()
    async def get_calendar_details(
        calendar_id: str,
        ctx: Context = None
    ) -> dict:
        """
        Obtiene detalles completos de un calendario específico.
        
        Args:
            calendar_id: ID del calendario
            
        Returns:
            Detalles del calendario incluyendo metadata y configuración
        """
        await ctx.info(f"Obteniendo detalles del calendario: {calendar_id}")
        
        service = get_service()
        
        calendar = service.calendars().get(calendarId=calendar_id).execute()
        
        return {
            "id": calendar.get("id"),
            "summary": calendar.get("summary"),
            "description": calendar.get("description", ""),
            "location": calendar.get("location", ""),
            "timezone": calendar.get("timeZone")
        }