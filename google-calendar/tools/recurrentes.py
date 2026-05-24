"""
Herramientas de eventos recurrentes para Google Calendar MCP

Este módulo contiene las tools para crear y gestionar eventos recurrentes.
"""

from fastmcp import Context
from helpers import get_service, build_recurrence_rule


def register_recurrentes_tools(mcp):
    """
    Registra todas las tools de eventos recurrentes en el servidor MCP.
    
    Args:
        mcp: Instancia de FastMCP
    """
    
    @mcp.tool()
    async def create_recurring_event(
        title: str,
        start: str,
        end: str,
        frequency: str,
        count: int = None,
        until: str = None,
        interval: int = 1,
        by_day: list[str] = None,
        description: str = "",
        location: str = "",
        calendar_id: str = "primary",
        ctx: Context = None
    ) -> dict:
        """
        Crea un evento recurrente en el calendario.
        
        Args:
            title: Título del evento
            start: Fecha/hora de inicio en ISO 8601
            end: Fecha/hora de fin en ISO 8601
            frequency: Frecuencia: DAILY, WEEKLY, MONTHLY, YEARLY
            count: Número de ocurrencias (opcional, mutuamente exclusivo con until)
            until: Fecha final en formato YYYYMMDD (opcional)
            interval: Intervalo de repetición (default: 1)
            by_day: Días de la semana [MO, TU, WE, TH, FR, SA, SU] (opcional)
            description: Descripción opcional
            location: Ubicación opcional
            calendar_id: ID del calendario (default: "primary")
            
        Returns:
            Evento recurrente creado con id, title, recurrence rule
            
        Examples:
            # Evento diario durante 10 días
            >>> await create_recurring_event(
            ...     "Ejercicio matutino",
            ...     "2026-04-10T07:00:00",
            ...     "2026-04-10T08:00:00",
            ...     "DAILY",
            ...     count=10
            ... )
            
            # Evento semanal los lunes y miércoles
            >>> await create_recurring_event(
            ...     "Clase de yoga",
            ...     "2026-04-10T18:00:00",
            ...     "2026-04-10T19:00:00",
            ...     "WEEKLY",
            ...     by_day=["MO", "WE"],
            ...     until="20261231"
            ... )
        """
        await ctx.info(f"Creando evento recurrente: {title}")
        
        service = get_service()
        
        # Construir regla de recurrencia
        rrule = build_recurrence_rule(
            frequency=frequency.upper(),
            count=count,
            until=until,
            interval=interval,
            by_day=by_day
        )
        
        event = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {"dateTime": start, "timeZone": "Europe/Madrid"},
            "end": {"dateTime": end, "timeZone": "Europe/Madrid"},
            "recurrence": [rrule]
        }
        
        result = service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()
        
        await ctx.info(f"Evento recurrente creado con ID: {result.get('id')}")
        
        return {
            "id": result.get("id"),
            "title": result.get("summary"),
            "start": result.get("start", {}).get("dateTime"),
            "end": result.get("end", {}).get("dateTime"),
            "recurrence": result.get("recurrence", []),
            "link": result.get("htmlLink")
        }