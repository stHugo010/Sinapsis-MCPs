"""
Funciones auxiliares para Telegram MCP

Este módulo contiene utilidades compartidas para envío de mensajes,
control de rate limiting y logging de notificaciones.
"""

import httpx
import asyncio
import time
from datetime import datetime

_last_call = 0
notification_log = []


async def send_message(base_url: str, chat_id: str, text: str) -> dict:
    """
    Envía un mensaje a Telegram con rate limiting.
    
    Args:
        base_url: URL base de la API de Telegram
        chat_id: ID del chat destino
        text: Contenido del mensaje (soporta Markdown)
        
    Returns:
        Respuesta JSON de la API de Telegram
    """
    global _last_call
    
    # Rate limiting: mínimo 100ms entre llamadas
    now = time.time()
    if now - _last_call < 0.1:
        await asyncio.sleep(0.1)
    _last_call = time.time()
    
    # Enviar mensaje
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
        )
        return response.json()


def get_timestamp() -> str:
    """
    Retorna timestamp formateado para mensajes.
    
    Returns:
        String con formato "DD/MM/YYYY · HH:MM"
    """
    return datetime.now().strftime("%d/%m/%Y · %H:%M")


def log_notification(source: str, action: str, reason: str):
    """
    Registra una notificación en el log de sesión.
    
    Args:
        source: Fuente de la notificación (obsidian, calendar, notion, system)
        action: Descripción de la acción realizada
        reason: Razón de la acción
    """
    notification_log.append({
        "source": source,
        "action": action,
        "reason": reason,
        "ts": datetime.now().isoformat()
    })


def get_notification_log() -> list[dict]:
    """
    Retorna el log completo de notificaciones de la sesión.
    
    Returns:
        Lista de notificaciones con metadata
    """
    return notification_log


def get_filtered_log(source: str) -> list[dict]:
    """
    Retorna el log filtrado por fuente.
    
    Args:
        source: Fuente a filtrar (obsidian, calendar, notion, system)
        
    Returns:
        Lista de notificaciones de la fuente especificada
    """
    return [n for n in notification_log if n["source"] == source]