"""
Funciones auxiliares para Google Calendar MCP

Este módulo contiene utilidades para autenticación OAuth2,
formateo de fechas, validaciones y helpers compartidos.
"""

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")


def get_service():
    """
    Obtiene el servicio autenticado de Google Calendar API.
    
    Carga las credenciales desde token.json y refresca si es necesario.
    
    Returns:
        Servicio autenticado de Google Calendar v3
        
    Raises:
        FileNotFoundError: Si token.json no existe
    """
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(
            f"No se encontró {TOKEN_PATH}. Ejecuta auth_setup.py primero."
        )
    
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # Refrescar token si está expirado
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    
    return build("calendar", "v3", credentials=creds)


def format_datetime_iso(dt: datetime) -> str:
    """
    Formatea un datetime a ISO 8601 con zona horaria.
    
    Args:
        dt: Objeto datetime
        
    Returns:
        String en formato ISO 8601
    """
    return dt.isoformat()


def parse_datetime_iso(iso_string: str) -> datetime:
    """
    Parsea un string ISO 8601 a datetime.
    
    Args:
        iso_string: String en formato ISO 8601
        
    Returns:
        Objeto datetime
    """
    # Manejar formato con Z (UTC)
    if iso_string.endswith('Z'):
        iso_string = iso_string.replace('Z', '+00:00')
    
    return datetime.fromisoformat(iso_string)


def validate_datetime_format(iso_string: str) -> bool:
    """
    Valida que un string tenga formato ISO 8601 válido.
    
    Args:
        iso_string: String a validar
        
    Returns:
        True si es válido, False en caso contrario
    """
    try:
        parse_datetime_iso(iso_string)
        return True
    except (ValueError, AttributeError):
        return False


def create_date_range(date: str, start_hour: int = 0, end_hour: int = 23) -> tuple:
    """
    Crea un rango de tiempo para una fecha específica.
    
    Args:
        date: Fecha en formato YYYY-MM-DD
        start_hour: Hora de inicio (0-23)
        end_hour: Hora de fin (0-23)
        
    Returns:
        Tupla (time_min, time_max) en formato ISO 8601
    """
    time_min = f"{date}T{start_hour:02d}:00:00+01:00"
    time_max = f"{date}T{end_hour:02d}:59:59+01:00"
    return time_min, time_max


def format_event_simple(event: dict) -> dict:
    """
    Formatea un evento de la API a formato simplificado.
    
    Args:
        event: Evento raw de Google Calendar API
        
    Returns:
        Diccionario con campos simplificados
    """
    return {
        "id": event.get("id"),
        "title": event.get("summary", "Sin título"),
        "start": event.get("start", {}).get("dateTime", event.get("start", {}).get("date")),
        "end": event.get("end", {}).get("dateTime", event.get("end", {}).get("date")),
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "color": event.get("colorId"),
        "calendar_id": event.get("organizer", {}).get("email", "primary")
    }


def calculate_free_slots(
    busy_blocks: List[dict],
    time_min: str,
    time_max: str,
    duration_minutes: int
) -> List[dict]:
    """
    Calcula huecos libres entre bloques ocupados.
    
    Args:
        busy_blocks: Lista de bloques ocupados con 'start' y 'end'
        time_min: Inicio del rango en ISO 8601
        time_max: Fin del rango en ISO 8601
        duration_minutes: Duración mínima del hueco
        
    Returns:
        Lista de huecos libres con start, end y duration_minutes
    """
    free_slots = []
    current = parse_datetime_iso(time_min)
    end = parse_datetime_iso(time_max)
    duration = timedelta(minutes=duration_minutes)
    
    for block in busy_blocks:
        block_start = parse_datetime_iso(block["start"])
        
        # Si hay espacio entre current y el inicio del bloque
        if block_start - current >= duration:
            free_slots.append({
                "start": format_datetime_iso(current),
                "end": format_datetime_iso(block_start),
                "duration_minutes": int((block_start - current).total_seconds() / 60)
            })
        
        # Actualizar current al final del bloque
        current = parse_datetime_iso(block["end"])
    
    # Espacio final después del último bloque
    if end - current >= duration:
        free_slots.append({
            "start": format_datetime_iso(current),
            "end": format_datetime_iso(end),
            "duration_minutes": int((end - current).total_seconds() / 60)
        })
    
    return free_slots


def build_recurrence_rule(
    frequency: str,
    count: Optional[int] = None,
    until: Optional[str] = None,
    interval: int = 1,
    by_day: Optional[List[str]] = None
) -> str:
    """
    Construye una regla RRULE para eventos recurrentes.
    
    Args:
        frequency: DAILY, WEEKLY, MONTHLY, YEARLY
        count: Número de ocurrencias (opcional)
        until: Fecha final en formato YYYYMMDD (opcional)
        interval: Intervalo de repetición (default: 1)
        by_day: Lista de días (MO, TU, WE, TH, FR, SA, SU)
        
    Returns:
        String RRULE válido
        
    Example:
        >>> build_recurrence_rule("WEEKLY", count=10, by_day=["MO", "WE", "FR"])
        "RRULE:FREQ=WEEKLY;COUNT=10;BYDAY=MO,WE,FR"
    """
    parts = [f"FREQ={frequency}"]
    
    if interval > 1:
        parts.append(f"INTERVAL={interval}")
    
    if count:
        parts.append(f"COUNT={count}")
    elif until:
        parts.append(f"UNTIL={until}")
    
    if by_day:
        parts.append(f"BYDAY={','.join(by_day)}")
    
    return "RRULE:" + ";".join(parts)


# Mapeo de colores de Google Calendar
CALENDAR_COLORS = {
    "lavender": "1",
    "sage": "2",
    "grape": "3",
    "flamingo": "4",
    "banana": "5",
    "tangerine": "6",
    "peacock": "7",
    "graphite": "8",
    "blueberry": "9",
    "basil": "10",
    "tomato": "11"
}


def get_color_id(color_name: str) -> Optional[str]:
    """
    Obtiene el ID de color para Google Calendar.
    
    Args:
        color_name: Nombre del color (lavender, sage, grape, etc.)
        
    Returns:
        ID del color o None si no existe
    """
    return CALENDAR_COLORS.get(color_name.lower())


def get_color_name(color_id: str) -> str:
    """
    Obtiene el nombre del color desde su ID.
    
    Args:
        color_id: ID del color (1-11)
        
    Returns:
        Nombre del color o "default" si no existe
    """
    for name, cid in CALENDAR_COLORS.items():
        if cid == color_id:
            return name
    return "default"