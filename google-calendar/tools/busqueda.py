"""
Herramientas de búsqueda avanzada para Google Calendar MCP

Este módulo contiene las tools para buscar huecos libres, detectar conflictos
y buscar eventos por texto.
"""

from fastmcp import Context
from helpers import (
    get_service,
    format_event_simple,
    create_date_range,
    calculate_free_slots,
    parse_datetime_iso
)
from datetime import datetime, timedelta


def register_busqueda_tools(mcp):
    """
    Registra todas las tools de búsqueda en el servidor MCP.
    
    Args:
        mcp: Instancia de FastMCP
    """
    
    @mcp.tool()
    async def find_free_slots(
        date: str,
        duration_minutes: int = 60,
        start_hour: int = 9,
        end_hour: int = 20,
        calendar_id: str = "primary",
        ctx: Context = None
    ) -> list[dict]:
        """
        Busca huecos libres en una fecha dada.
        
        Args:
            date: Fecha en formato YYYY-MM-DD
            duration_minutes: Duración mínima del hueco en minutos (default: 60)
            start_hour: Hora de inicio del rango (0-23, default: 9)
            end_hour: Hora de fin del rango (0-23, default: 20)
            calendar_id: ID del calendario (default: "primary")
            
        Returns:
            Lista de huecos libres con start, end, duration_minutes
            
        Example:
            >>> await find_free_slots("2026-04-10", 60, 9, 18)
            [{"start": "2026-04-10T09:00:00+01:00", "end": "2026-04-10T10:30:00+01:00", "duration_minutes": 90}]
        """
        await ctx.info(f"Buscando huecos de {duration_minutes} min el {date}...")
        
        service = get_service()
        time_min, time_max = create_date_range(date, start_hour, end_hour)
        
        # Consultar bloques ocupados
        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": calendar_id}]
        }
        
        result = service.freebusy().query(body=body).execute()
        busy_blocks = result["calendars"][calendar_id]["busy"]
        
        # Calcular huecos libres
        free_slots = calculate_free_slots(
            busy_blocks,
            time_min,
            time_max,
            duration_minutes
        )
        
        await ctx.info(f"Encontrados {len(free_slots)} huecos libres")
        
        return free_slots
    
    
    @mcp.tool()
    async def search_events(
        query: str,
        time_min: str = None,
        time_max: str = None,
        calendar_id: str = "primary",
        max_results: int = 20,
        ctx: Context = None
    ) -> list[dict]:
        """
        Busca eventos por texto en título o descripción.
        
        Args:
            query: Texto a buscar
            time_min: Fecha/hora mínima en ISO 8601 (opcional)
            time_max: Fecha/hora máxima en ISO 8601 (opcional)
            calendar_id: ID del calendario (default: "primary")
            max_results: Número máximo de resultados (default: 20)
            
        Returns:
            Lista de eventos que coinciden con la búsqueda
            
        Example:
            >>> await search_events("TFG", time_min="2026-04-01T00:00:00")
            [{"id": "abc", "title": "Reunión TFG", ...}]
        """
        await ctx.info(f"Buscando eventos con query: {query}")
        
        service = get_service()
        
        # Si no se especifica rango, buscar desde ahora
        if not time_min:
            time_min = datetime.utcnow().isoformat() + "Z"
        
        params = {
            "calendarId": calendar_id,
            "q": query,
            "timeMin": time_min,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        
        if time_max:
            params["timeMax"] = time_max
        
        result = service.events().list(**params).execute()
        events = result.get("items", [])
        
        await ctx.info(f"Encontrados {len(events)} eventos")
        
        return [format_event_simple(e) for e in events]
    
    
    @mcp.tool()
    async def find_conflicts(
        start: str,
        end: str,
        calendar_ids: list[str] = None,
        ctx: Context = None
    ) -> list[dict]:
        """
        Detecta eventos que se solapan con un rango de tiempo.
        
        Útil para verificar conflictos antes de crear un evento.
        
        Args:
            start: Fecha/hora de inicio en ISO 8601
            end: Fecha/hora de fin en ISO 8601
            calendar_ids: Lista de IDs de calendarios (default: ["primary"])
            
        Returns:
            Lista de eventos que se solapan con el rango especificado
            
        Example:
            >>> await find_conflicts(
            ...     "2026-04-10T10:00:00",
            ...     "2026-04-10T11:00:00"
            ... )
            [{"id": "abc", "title": "Reunión que se solapa", ...}]
        """
        await ctx.info(f"Detectando conflictos entre {start} y {end}")
        
        service = get_service()
        
        if not calendar_ids:
            calendar_ids = ["primary"]
        
        # Construir query freebusy
        body = {
            "timeMin": start,
            "timeMax": end,
            "items": [{"id": cal_id} for cal_id in calendar_ids]
        }
        
        result = service.freebusy().query(body=body).execute()
        
        # Recopilar todos los eventos que se solapan
        conflicts = []
        
        for cal_id in calendar_ids:
            busy_blocks = result["calendars"][cal_id].get("busy", [])
            
            if busy_blocks:
                # Obtener detalles de los eventos ocupados
                for block in busy_blocks:
                    # Buscar eventos en ese rango
                    events = service.events().list(
                        calendarId=cal_id,
                        timeMin=block["start"],
                        timeMax=block["end"],
                        singleEvents=True
                    ).execute()
                    
                    for event in events.get("items", []):
                        conflicts.append(format_event_simple(event))
        
        await ctx.info(f"Encontrados {len(conflicts)} conflictos")
        
        return conflicts
    
    
    @mcp.tool()
    async def get_busy_times(
        date_start: str,
        date_end: str,
        calendar_ids: list[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Obtiene todos los bloques ocupados en un rango de fechas.
        
        Útil para coordinación con otras personas o análisis de disponibilidad.
        
        Args:
            date_start: Fecha de inicio en formato YYYY-MM-DD
            date_end: Fecha de fin en formato YYYY-MM-DD
            calendar_ids: Lista de IDs de calendarios (default: ["primary"])
            
        Returns:
            Diccionario con bloques ocupados por calendario
            
        Example:
            >>> await get_busy_times("2026-04-10", "2026-04-12")
            {
                "primary": [
                    {"start": "2026-04-10T10:00:00+02:00", "end": "2026-04-10T11:00:00+02:00"},
                    ...
                ]
            }
        """
        await ctx.info(f"Obteniendo bloques ocupados del {date_start} al {date_end}")
        
        service = get_service()
        
        if not calendar_ids:
            calendar_ids = ["primary"]
        
        time_min = f"{date_start}T00:00:00+01:00"
        time_max = f"{date_end}T23:59:59+01:00"
        
        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": cal_id} for cal_id in calendar_ids]
        }
        
        result = service.freebusy().query(body=body).execute()
        
        busy_times = {}
        for cal_id in calendar_ids:
            busy_times[cal_id] = result["calendars"][cal_id].get("busy", [])
        
        total_blocks = sum(len(blocks) for blocks in busy_times.values())
        await ctx.info(f"Encontrados {total_blocks} bloques ocupados")
        
        return busy_times