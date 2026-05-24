"""
constants.py
Constantes y configuraciones del sistema de monitorización Sentinel
"""

from enum import Enum
from typing import Final

# ─── Límites de herramientas ─────────────────────────────────────────────────
PROCESS_LIMIT_MIN: Final[int] = 1
PROCESS_LIMIT_MAX: Final[int] = 50
PROCESS_LIMIT_DEFAULT: Final[int] = 10

LOG_LINES_MIN: Final[int] = 10
LOG_LINES_MAX: Final[int] = 500
LOG_LINES_DEFAULT: Final[int] = 100

HISTORY_SAMPLES_MIN: Final[int] = 1
HISTORY_SAMPLES_MAX: Final[int] = 1440  # 24 horas con 1 muestra/minuto
HISTORY_SAMPLES_DEFAULT: Final[int] = 60

PERFORMANCE_INTERVAL_MIN: Final[int] = 10  # segundos
PERFORMANCE_INTERVAL_MAX: Final[int] = 3600  # 1 hora
PERFORMANCE_INTERVAL_DEFAULT: Final[int] = 60

LOG_TIME_MIN: Final[int] = 1  # minutos
LOG_TIME_MAX: Final[int] = 1440  # 24 horas

# ─── Umbrales de alerta ──────────────────────────────────────────────────────
CPU_ALERT_THRESHOLD: Final[float] = 80.0  # %
RAM_ALERT_THRESHOLD: Final[float] = 85.0  # %
DISK_ALERT_THRESHOLD: Final[float] = 90.0  # %
TEMP_WARNING_THRESHOLD: Final[float] = 75.0  # °C
TEMP_CRITICAL_THRESHOLD: Final[float] = 85.0  # °C

GPU_UTIL_HIGH: Final[float] = 80.0  # %
GPU_UTIL_CRITICAL: Final[float] = 95.0  # %
GPU_TEMP_HIGH: Final[float] = 75.0  # °C
GPU_TEMP_CRITICAL: Final[float] = 85.0  # °C

BATTERY_LOW: Final[float] = 20.0  # %
BATTERY_CRITICAL: Final[float] = 10.0  # %

# ─── Procesos críticos del sistema (NUNCA terminar) ──────────────────────────
CRITICAL_PROCESSES: Final[list[str]] = [
    "systemd",
    "init",
    "kernel",
    "kthreadd",
    "sshd",
    "NetworkManager",
    "dbus-daemon",
    "systemd-logind",
    "systemd-journald",
    "systemd-udevd",
]

CRITICAL_PROCESS_OWNERS: Final[list[str]] = [
    "root",
    "systemd-network",
    "systemd-resolve",
]

# ─── Enums para tipos ─────────────────────────────────────────────────────────
class SortCriteria(str, Enum):
    """Criterios de ordenación para procesos"""
    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"

class LogLevel(str, Enum):
    """Niveles de log del sistema"""
    ALL = "all"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class MetricType(str, Enum):
    """Tipos de métricas de rendimiento"""
    CPU = "cpu"
    RAM = "ram"
    BOTH = "both"

class SamplerAction(str, Enum):
    """Acciones del sampler de rendimiento"""
    START = "start"
    STOP = "stop"
    CLEAR = "clear"
    STATUS = "status"

class SystemStatus(str, Enum):
    """Estados del sistema"""
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"

# ─── Mensajes del sistema ─────────────────────────────────────────────────────
GUARDIAN_BLOCKED_MSG: Final[str] = "Operación bloqueada por el guardian de seguridad"
PERMISSION_DENIED_MSG: Final[str] = "Permisos insuficientes para esta operación"
GPU_NOT_DETECTED_MSG: Final[str] = "No se detectó GPU compatible"
BATTERY_NOT_DETECTED_MSG: Final[str] = "No se detectó batería (sistema de escritorio o sin soporte)"
FANS_NOT_DETECTED_MSG: Final[str] = "No se detectaron sensores de ventiladores"

# ─── Instrucciones del servidor MCP ───────────────────────────────────────────
MCP_INSTRUCTIONS: Final[str] = """
Eres un asistente de diagnóstico del sistema. Tienes acceso a herramientas
para monitorizar el estado del sistema operativo Linux en tiempo real.

REGLAS DE SEGURIDAD IMPORTANTES:
- NUNCA mates procesos del sistema críticos (kernel, init, systemd, sshd, etc.)
- Siempre confirma con el usuario antes de ejecutar terminate_process
- Los datos se procesan localmente; no envíes información sensible al exterior
- Si un proceso requiere permisos de root, informa al usuario

CAPACIDADES:
- Monitorización de CPU, RAM, disco, swap y temperaturas
- Listado y gestión de procesos en ejecución
- Análisis de logs del sistema (journalctl/syslog)
- Monitorización de conexiones de red activas
- Información de hardware: batería, ventiladores, GPU
- Historial de rendimiento con detección de picos
"""