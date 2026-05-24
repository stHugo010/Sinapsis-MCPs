"""
Resources para Google Calendar MCP

Este módulo contiene los endpoints de solo lectura que exponen
eventos de hoy y de la semana.
"""

from helpers import get_service
from datetime import datetime, timedelta
import json


def register_resources(mcp):
    """
    Registra todos los resources del Google Calendar MCP.
    
    Args:
        mcp: Instancia de FastMCP
    """
    
    @mcp.resource("calendar://today")
    async def get_today_events() -> str:
        """
        Eventos del día actual.
        
        Returns:
            JSON con lista de eventos de hoy
        """
        service = get_service()
        
        today = datetime.now().strftime("%Y-%m-%d")
        time_min = f"{today}T00:00:00+01:00"
        time_max = f"{today}T23:59:59+01:00"
        
        result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        events = [
            {
                "title": e.get("summary"),
                "start": e.get("start", {}).get("dateTime"),
                "end": e.get("end", {}).get("dateTime"),
                "location": e.get("location", "")
            }
            for e in result.get("items", [])
        ]
        
        return json.dumps(events, indent=2, ensure_ascii=False)
    
    
    @mcp.resource("calendar://week")
    async def get_week_events() -> str:
        """
        Eventos de los próximos 7 días.
        
        Returns:
            JSON con lista de eventos de la semana
        """
        service = get_service()
        
        now = datetime.utcnow().isoformat() + "Z"
        week = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
        
        result = service.events().list(
            calendarId="primary",
            timeMin=now,
            timeMax=week,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        events = [
            {
                "title": e.get("summary"),
                "start": e.get("start", {}).get("dateTime"),
                "end": e.get("end", {}).get("dateTime"),
                "location": e.get("location", "")
            }
            for e in result.get("items", [])
        ]
        
        return json.dumps(events, indent=2, ensure_ascii=False)