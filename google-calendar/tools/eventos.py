"""
Herramientas de gestión de eventos para Google Calendar MCP

Este módulo contiene las tools para crear, leer, modificar y eliminar eventos.
"""

from fastmcp import Context
from helpers import get_service, format_event_simple


def register_eventos_tools(mcp):
    """
    Registra todas las tools de gestión de eventos en el servidor MCP.
    
    Args:
        mcp: Instancia de FastMCP
    """
    
    @mcp.tool()
    async def list_events(
        max_results: int = 10,
        calendar_id: str = "primary",
        ctx: Context = None
    ) -> list[dict]:
        """
        Lista los próximos eventos de un calendario.
        
        Args:
            max_results: Número máximo de eventos a retornar (default: 10)
            calendar_id: ID del calendario (default: "primary")
            
        Returns:
            Lista de eventos con id, title, start, end, description
            
        Example:
            >>> await list_events(5)
            [{"id": "abc123", "title": "Reunión", "start": "2026-04-10T10:00:00+02:00", ...}]
        """
        await ctx.info(f"Listando próximos {max_results} eventos del calendario {calendar_id}...")
        
        service = get_service()
        from datetime import datetime
        
        now = datetime.utcnow().isoformat() + "Z"
        
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        events = result.get("items", [])
        await ctx.info(f"Encontrados {len(events)} eventos")
        
        return [format_event_simple(e) for e in events]
    
    
    @mcp.tool()
    async def create_event(
        title: str,
        start: str,
        end: str,
        description: str = "",
        location: str = "",
        calendar_id: str = "primary",
        ctx: Context = None
    ) -> dict:
        """
        Crea un evento en el calendario.
        
        Args:
            title: Título del evento
            start: Fecha/hora de inicio en formato ISO 8601 (ej: '2026-04-10T10:00:00')
            end: Fecha/hora de fin en formato ISO 8601
            description: Descripción opcional del evento
            location: Ubicación opcional del evento
            calendar_id: ID del calendario (default: "primary")
            
        Returns:
            Evento creado con id, title, start, end, link
            
        Example:
            >>> await create_event(
            ...     "Reunión TFG",
            ...     "2026-04-10T10:00:00",
            ...     "2026-04-10T11:00:00",
            ...     description="Revisión de avances"
            ... )
        """
        await ctx.info(f"Creando evento: {title}")
        
        service = get_service()
        
        event = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {"dateTime": start, "timeZone": "Europe/Madrid"},
            "end": {"dateTime": end, "timeZone": "Europe/Madrid"},
        }
        
        result = service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()
        
        await ctx.info(f"Evento creado con ID: {result.get('id')}")
        
        return {
            "id": result.get("id"),
            "title": result.get("summary"),
            "start": result.get("start", {}).get("dateTime"),
            "end": result.get("end", {}).get("dateTime"),
            "link": result.get("htmlLink")
        }
    
    
    @mcp.tool()
    async def update_event(
        event_id: str,
        title: str = None,
        start: str = None,
        end: str = None,
        description: str = None,
        location: str = None,
        calendar_id: str = "primary",
        ctx: Context = None
    ) -> dict:
        """
        Modifica un evento existente.
        
        Solo actualiza los campos proporcionados, el resto permanece sin cambios.
        
        Args:
            event_id: ID del evento a modificar
            title: Nuevo título (opcional)
            start: Nueva fecha/hora de inicio (opcional)
            end: Nueva fecha/hora de fin (opcional)
            description: Nueva descripción (opcional)
            location: Nueva ubicación (opcional)
            calendar_id: ID del calendario (default: "primary")
            
        Returns:
            Evento actualizado con id, title, link
        """
        await ctx.info(f"Actualizando evento: {event_id}")
        
        service = get_service()
        
        # Obtener evento actual
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        # Actualizar solo los campos proporcionados
        if title:
            event["summary"] = title
        if description is not None:
            event["description"] = description
        if location is not None:
            event["location"] = location
        if start:
            event["start"] = {"dateTime": start, "timeZone": "Europe/Madrid"}
        if end:
            event["end"] = {"dateTime": end, "timeZone": "Europe/Madrid"}
        
        # Guardar cambios
        result = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()
        
        await ctx.info("Evento actualizado correctamente")
        
        return {
            "id": result.get("id"),
            "title": result.get("summary"),
            "link": result.get("htmlLink")
        }
    
    
    @mcp.tool()
    async def delete_event(
        event_id: str,
        calendar_id: str = "primary",
        ctx: Context = None
    ) -> dict:
        """
        Elimina un evento del calendario.
        
        Args:
            event_id: ID del evento a eliminar
            calendar_id: ID del calendario (default: "primary")
            
        Returns:
            Confirmación de eliminación con event_id
            
        Warning:
            Esta operación no es reversible
        """
        await ctx.info(f"Eliminando evento: {event_id}")
        
        service = get_service()
        
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        await ctx.info("Evento eliminado")
        
        return {"deleted": True, "event_id": event_id}