"""
core/logs.py
Análisis de logs del sistema (journalctl y syslog)
"""

import subprocess
from typing import Dict, Any, List

from ..utils import now_iso
from ..constants import LogLevel


def analyze_logs(
    lines: int = 100,
    level: str = "error",
    since_minutes: int = 60,
) -> Dict[str, Any]:
    """
    Analiza logs del sistema buscando errores.
    
    Args:
        lines: Número de líneas a retornar
        level: Nivel mínimo ("error", "warning", "info", "all")
        since_minutes: Ventana de tiempo en minutos
    
    Returns:
        Dict con entradas de log filtradas
    """
    # Construir comando journalctl
    priority_map = {
        LogLevel.ERROR: "3",     # err
        LogLevel.WARNING: "4",   # warning
        LogLevel.INFO: "6",      # info
        LogLevel.ALL: "7",       # debug
    }
    
    priority = priority_map.get(level, "3")
    
    cmd = [
        "journalctl",
        "--no-pager",
        "-p", priority,
        "--since", f"{since_minutes} minutes ago",
        "-n", str(lines),
        "--output=json",
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode != 0:
            # Fallback a syslog si journalctl falla
            return _analyze_syslog(lines, level)
        
        # Parsear JSON de journalctl
        import json
        log_entries = []
        
        for line in result.stdout.strip().splitlines():
            try:
                entry = json.loads(line)
                log_entries.append({
                    "timestamp": entry.get("__REALTIME_TIMESTAMP", "unknown"),
                    "priority": entry.get("PRIORITY", "unknown"),
                    "unit": entry.get("_SYSTEMD_UNIT", "unknown"),
                    "message": entry.get("MESSAGE", ""),
                })
            except json.JSONDecodeError:
                continue
        
        return {
            "timestamp": now_iso(),
            "source": "journalctl",
            "level_filter": level,
            "since_minutes": since_minutes,
            "total_entries": len(log_entries),
            "entries": log_entries,
        }
    
    except subprocess.TimeoutExpired:
        return {
            "error": "Timeout al leer logs",
            "hint": "El sistema puede estar bajo carga alta",
        }
    except PermissionError:
        return {
            "error": "Permisos insuficientes",
            "hint": "Ejecuta el servidor MCP con sudo para acceder a logs del sistema",
        }
    except Exception as e:
        return {
            "error": f"Error al analizar logs: {str(e)}",
        }


def _analyze_syslog(lines: int, level: str) -> Dict[str, Any]:
    """Fallback: analiza /var/log/syslog si journalctl no está disponible"""
    try:
        with open("/var/log/syslog", "r") as f:
            log_lines = f.readlines()[-lines:]
        
        # Filtrado simple por nivel
        filtered = []
        for line in log_lines:
            line_lower = line.lower()
            if level == LogLevel.ERROR and "error" in line_lower:
                filtered.append(line.strip())
            elif level == LogLevel.WARNING and ("warning" in line_lower or "error" in line_lower):
                filtered.append(line.strip())
            elif level == LogLevel.INFO or level == LogLevel.ALL:
                filtered.append(line.strip())
        
        return {
            "timestamp": now_iso(),
            "source": "syslog",
            "level_filter": level,
            "total_entries": len(filtered),
            "entries": [{"message": line} for line in filtered],
        }
    
    except PermissionError:
        raise PermissionError("Permisos insuficientes para leer /var/log/syslog")
    except FileNotFoundError:
        return {
            "error": "No se pudo acceder a logs del sistema",
            "hint": "journalctl y /var/log/syslog no disponibles",
        }