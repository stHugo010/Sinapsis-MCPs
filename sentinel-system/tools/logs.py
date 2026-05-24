"""
tools/logs.py
Lectura y filtrado de logs del sistema Linux mediante journalctl.
"""

import re
import subprocess
from datetime import datetime, timedelta
from typing import Literal


# Patrones de errores relevantes que interesarán al LLM
_ERROR_PATTERNS = [
    r"error|Error|ERROR",
    r"fail(ed)?|Fail(ed)?|FAIL(ED)?",
    r"critical|Critical|CRITICAL",
    r"panic|Panic|PANIC",
    r"crash|Crash|CRASH",
    r"killed|oom|out.of.memory",
    r"segfault|segmentation",
    r"denied|permission",
    r"timeout|Timeout",
    r"disk.*full|no space",
]

_COMBINED_PATTERN = re.compile("|".join(_ERROR_PATTERNS), re.IGNORECASE)

# Niveles journalctl (0=emerg ... 7=debug)
_LEVEL_MAP: dict[str, str] = {
    "error":   "3",   # emerg, alert, crit, err
    "warning": "4",   # + warning
    "info":    "6",   # + notice, info
    "all":     "7",   # + debug
}


def analyze_logs(
    lines: int = 100,
    level: Literal["error", "warning", "info", "all"] = "error",
    since_minutes: int = 60,
) -> dict:
    """
    Lee logs del sistema usando journalctl.
    Retorna entradas parseadas con estadísticas de errores.
    
    Fallback: si journalctl no está disponible, intenta /var/log/syslog.
    """
    since_dt = datetime.now() - timedelta(minutes=since_minutes)
    since_str = since_dt.strftime("%Y-%m-%d %H:%M:%S")

    priority = _LEVEL_MAP.get(level, "3")

    # ── Intentar journalctl ───────────────────────────────────────────────────
    try:
        result = subprocess.run(
            [
                "journalctl",
                "--no-pager",
                "--output=short-iso",
                f"--priority={priority}",
                f"--since={since_str}",
                f"--lines={lines}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            raw_lines = result.stdout.strip().splitlines()
            return _parse_journalctl_output(raw_lines, level, since_minutes)

        # journalctl devuelve 1 si no hay entradas (no es error real)
        if result.returncode == 1 and not result.stderr:
            return {
                "source": "journalctl",
                "level_filter": level,
                "since_minutes": since_minutes,
                "total_entries": 0,
                "entries": [],
                "summary": "No se encontraron entradas para el filtro aplicado.",
            }

        raise RuntimeError(result.stderr)

    except FileNotFoundError:
        # journalctl no disponible → fallback a syslog
        return _read_syslog_fallback(lines=lines, level=level)
    except subprocess.TimeoutExpired:
        return {"error": "Timeout leyendo logs del sistema (>10s)"}
    except PermissionError:
        raise  # Lo manejamos arriba en server.py


def _parse_journalctl_output(raw_lines: list[str], level: str, since_minutes: int) -> dict:
    """Parsea la salida de journalctl en formato short-iso."""
    entries = []
    error_count = warning_count = 0

    for line in raw_lines:
        # Formato: 2025-03-14T12:34:56+0100 hostname unit[pid]: message
        parts = line.split(" ", 3)
        if len(parts) < 4:
            continue

        timestamp_str = parts[0]
        # hostname = parts[1]
        unit_pid      = parts[2].rstrip(":")
        message       = parts[3] if len(parts) > 3 else ""

        # Extraer unidad y PID
        unit, pid = unit_pid, None
        m = re.match(r"(.+)\[(\d+)\]", unit_pid)
        if m:
            unit, pid = m.group(1), int(m.group(2))

        # Detectar nivel real de la entrada
        entry_level = _detect_entry_level(message)
        if entry_level == "error":
            error_count += 1
        elif entry_level == "warning":
            warning_count += 1

        # Marcar si contiene patrones de error conocidos
        has_keyword = bool(_COMBINED_PATTERN.search(message))

        entries.append({
            "timestamp": timestamp_str,
            "unit":      unit,
            "pid":       pid,
            "level":     entry_level,
            "message":   message[:500],  # truncar mensajes muy largos
            "flagged":   has_keyword,
        })

    # Estadísticas generales
    flagged = [e for e in entries if e["flagged"]]
    units_with_errors = list({e["unit"] for e in entries if e["level"] == "error"})

    return {
        "source":          "journalctl",
        "level_filter":    level,
        "since_minutes":   since_minutes,
        "total_entries":   len(entries),
        "error_count":     error_count,
        "warning_count":   warning_count,
        "flagged_count":   len(flagged),
        "units_with_errors": units_with_errors[:10],  # máx 10 para brevedad
        "entries":         entries,
        "summary":         _build_summary(entries, error_count, warning_count, units_with_errors),
    }


def _read_syslog_fallback(lines: int, level: str) -> dict:
    """Lee /var/log/syslog como alternativa cuando journalctl no está disponible."""
    syslog_path = "/var/log/syslog"
    try:
        with open(syslog_path, "r", errors="replace") as f:
            all_lines = f.readlines()

        # Leer últimas N líneas
        recent = all_lines[-lines:]

        # Filtrar por nivel si se pide error/warning
        if level in ("error", "warning"):
            recent = [l for l in recent if _COMBINED_PATTERN.search(l)]

        entries = [
            {"raw": line.strip()[:300], "flagged": bool(_COMBINED_PATTERN.search(line))}
            for line in recent
        ]

        return {
            "source":        "syslog",
            "level_filter":  level,
            "total_entries": len(entries),
            "entries":       entries,
            "note":          "journalctl no disponible; usando /var/log/syslog sin parsear",
        }
    except FileNotFoundError:
        return {
            "error": "No se encontró journalctl ni /var/log/syslog",
            "hint":  "Este MCP está optimizado para sistemas Linux con systemd",
        }


def _detect_entry_level(message: str) -> str:
    msg_lower = message.lower()
    if any(k in msg_lower for k in ("error", "err", "crit", "emerg", "alert", "panic", "fatal")):
        return "error"
    if any(k in msg_lower for k in ("warning", "warn")):
        return "warning"
    return "info"


def _build_summary(entries: list, errors: int, warnings: int, units: list) -> str:
    if not entries:
        return "No hay entradas de log para el período analizado."
    parts = [f"Se analizaron {len(entries)} entradas de log."]
    if errors:
        parts.append(f"{errors} errores detectados.")
    if warnings:
        parts.append(f"{warnings} advertencias.")
    if units:
        parts.append(f"Unidades con errores: {', '.join(units[:5])}.")
    return " ".join(parts)