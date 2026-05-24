"""
utils/helpers.py
Funciones de utilidad compartidas
"""

import datetime
from typing import Union


def now_iso() -> str:
    """Retorna timestamp actual en formato ISO"""
    return datetime.datetime.now().isoformat(timespec="seconds")


def safe_int(value: Union[str, int, float, None], default: int = 0) -> int:
    """Convierte valor a int de forma segura"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Union[str, int, float, None], default: float = 0.0) -> float:
    """Convierte valor a float de forma segura"""
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return default


def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """Limita un valor entre min y max"""
    return max(min_val, min(max_val, value))


def bytes_to_gb(bytes_val: int, decimals: int = 2) -> float:
    """Convierte bytes a GB"""
    return round(bytes_val / 1e9, decimals)


def bytes_to_mb(bytes_val: int, decimals: int = 1) -> float:
    """Convierte bytes a MB"""
    return round(bytes_val / 1e6, decimals)


def format_time_left(seconds: int) -> str:
    """Formatea segundos restantes en formato legible"""
    if seconds < 0:
        return "desconocido"
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def is_external_ip(ip: str) -> bool:
    """Verifica si una IP es externa (no localhost/LAN)"""
    if not ip:
        return False
    
    # Localhost
    if ip.startswith("127.") or ip == "::1" or ip == "localhost":
        return False
    
    # Redes privadas
    if ip.startswith("10.") or ip.startswith("172.16.") or ip.startswith("192.168."):
        return False
    
    # Link-local
    if ip.startswith("169.254.") or ip.startswith("fe80:"):
        return False
    
    return True