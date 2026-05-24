"""
System Sentinel - MCP Server para monitorización del sistema
TFG: Integración de LLMs con herramientas de diagnóstico del sistema operativo

Uso:
    python server.py          # Modo stdio (para Claude Desktop)
    python server.py --dev    # Modo debug con logs
"""

import asyncio
import json
import logging
import sys
from mcp.server.fastmcp import FastMCP

from tools.health import get_system_health
from tools.processes import list_processes, kill_process
from tools.logs import analyze_logs
from tools.network import get_network_stats
from tools.guardian import ProcessGuardian
from tools.performance import (
    get_performance_history,
    start_performance_sampler,
    stop_performance_sampler,
    clear_performance_history,
)

# ─── Configuración de logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if "--dev" in sys.argv else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,  # MCP usa stdout para el protocolo; logs van a stderr
)
logger = logging.getLogger("system-sentinel")

# ─── Instancia del servidor MCP ───────────────────────────────────────────────
mcp = FastMCP(
    "system-sentinel",
    instructions="""
    Eres un asistente de diagnóstico del sistema. Tienes acceso a herramientas
    para monitorizar el estado del sistema operativo Linux en tiempo real.
    
    REGLAS DE SEGURIDAD IMPORTANTES:
    - NUNCA mates procesos del sistema críticos (kernel, init, systemd, sshd, etc.)
    - Siempre confirma con el usuario antes de ejecutar kill_process
    - Los datos se procesan localmente; no envíes información sensible al exterior
    - Si un proceso requiere permisos de root, informa al usuario
    """,
)

guardian = ProcessGuardian()

# ─── TOOL 1: get_system_health ────────────────────────────────────────────────
@mcp.tool()
async def system_health() -> str:
    """
    Obtiene un snapshot completo del estado del sistema:
    CPU, RAM, disco, swap y temperaturas (si están disponibles).
    Útil para diagnóstico inicial cuando el sistema va lento o el ventilador ruge.
    """
    logger.info("Tool llamada: system_health")
    try:
        data = get_system_health()
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error en system_health: {e}")
        return json.dumps({"error": str(e)})


# ─── TOOL 2: list_processes ───────────────────────────────────────────────────
@mcp.tool()
async def top_processes(
    sort_by: str = "cpu",
    limit: int = 10,
    include_system: bool = False,
) -> str:
    """
    Lista los procesos que más recursos consumen.
    
    Args:
        sort_by: Criterio de ordenación. Opciones: "cpu", "memory", "io"
        limit: Número máximo de procesos a devolver (1-50)
        include_system: Si True, incluye procesos del sistema/kernel
    
    Returns:
        Lista de procesos con PID, nombre, usuario, %CPU, %RAM y estado
    """
    logger.info(f"Tool llamada: top_processes(sort_by={sort_by}, limit={limit})")
    limit = max(1, min(50, limit))  # Clamp entre 1 y 50
    
    try:
        data = list_processes(sort_by=sort_by, limit=limit, include_system=include_system)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error en top_processes: {e}")
        return json.dumps({"error": str(e)})


# ─── TOOL 3: kill_process ─────────────────────────────────────────────────────
@mcp.tool()
async def terminate_process(
    pid: int,
    force: bool = False,
    reason: str = "",
) -> str:
    """
    Termina un proceso del sistema por su PID.
    
    IMPORTANTE: Esta herramienta tiene impacto real en el sistema.
    Úsala solo cuando el usuario haya confirmado explícitamente.
    
    Args:
        pid: ID del proceso a terminar (obligatorio)
        force: Si True, usa SIGKILL (forzado). Si False, usa SIGTERM (graceful)
        reason: Razón por la que se termina el proceso (para el log de auditoría)
    
    Returns:
        Resultado de la operación con el estado del proceso antes/después
    """
    logger.info(f"Tool llamada: terminate_process(pid={pid}, force={force})")
    
    # Verificación de seguridad ANTES de actuar
    check = guardian.is_safe_to_kill(pid)
    if not check["safe"]:
        return json.dumps({
            "success": False,
            "blocked": True,
            "reason": check["reason"],
            "message": f"Operación bloqueada por el guardian de seguridad: {check['reason']}",
        })
    
    try:
        result = kill_process(pid=pid, force=force)
        # Log de auditoría
        logger.warning(
            f"AUDITORÍA: Proceso terminado | PID={pid} | "
            f"Nombre={result.get('name', 'desconocido')} | "
            f"Force={force} | Razón='{reason}'"
        )
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error en terminate_process: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ─── TOOL 4: analyze_logs ────────────────────────────────────────────────────
@mcp.tool()
async def read_system_logs(
    lines: int = 100,
    level: str = "error",
    since_minutes: int = 60,
) -> str:
    """
    Lee y filtra los logs del sistema (journalctl / syslog) buscando errores.
    
    Args:
        lines: Número máximo de líneas a devolver (10-500)
        level: Nivel mínimo de log. Opciones: "error", "warning", "info", "all"
        since_minutes: Analizar logs de los últimos N minutos (1-1440)
    
    Returns:
        Entradas de log filtradas con timestamp, nivel y mensaje
    
    Nota: Puede requerir permisos de root para ciertos logs del sistema.
    """
    logger.info(f"Tool llamada: read_system_logs(lines={lines}, level={level})")
    lines = max(10, min(500, lines))
    since_minutes = max(1, min(1440, since_minutes))
    
    try:
        data = analyze_logs(lines=lines, level=level, since_minutes=since_minutes)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except PermissionError:
        return json.dumps({
            "error": "Permisos insuficientes",
            "hint": "Ejecuta el servidor MCP con sudo para acceder a logs del sistema",
        })
    except Exception as e:
        logger.error(f"Error en read_system_logs: {e}")
        return json.dumps({"error": str(e)})


# ─── TOOL 5: network_stats ───────────────────────────────────────────────────
@mcp.tool()
async def network_connections(
    show_listening: bool = True,
    show_established: bool = True,
    flag_external: bool = True,
) -> str:
    """
    Muestra conexiones de red activas y consumo de ancho de banda por proceso.
    Útil para detectar procesos sospechosos conectados a IPs externas.
    
    Args:
        show_listening: Incluir puertos en escucha (servidores locales)
        show_established: Incluir conexiones establecidas
        flag_external: Marcar conexiones a IPs externas (no LAN/localhost)
    
    Returns:
        Lista de conexiones con proceso, IP local/remota, estado y si es externa
    """
    logger.info("Tool llamada: network_connections")
    try:
        data = get_network_stats(
            show_listening=show_listening,
            show_established=show_established,
            flag_external=flag_external,
        )
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error en network_connections: {e}")
        return json.dumps({"error": str(e)})

# ─── TOOL 6: hardware_info ───────────────────────────────────────────────────
@mcp.tool()
async def hardware_info(
    include_battery: bool = True,
    include_fans: bool = True,
    include_gpu: bool = True,
) -> str:
    """
    Información detallada del hardware físico: batería, ventiladores, GPU y memoria.
    Detecta automáticamente NVIDIA (nvidia-smi), AMD (rocm-smi) e Intel integrada.
 
    Args:
        include_battery: Incluir estado de batería (nivel, tiempo restante, si carga)
        include_fans: Incluir RPM de ventiladores por sensor
        include_gpu: Incluir uso/temperatura/VRAM de GPU
 
    Returns:
        Hardware snapshot con batería, fans, GPU, detalle de CPU por núcleo y memoria
    """
    logger.info("Tool llamada: hardware_info")
    try:
        data = get_hardware_info(
            include_battery=include_battery,
            include_fans=include_fans,
            include_gpu=include_gpu,
        )
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error en hardware_info: {e}")
        return json.dumps({"error": str(e)})
 
 
# ─── TOOL 7: performance_history ─────────────────────────────────────────────
@mcp.tool()
async def performance_history(
    last_n: int = 60,
    metric: str = "both",
    alert_cpu_threshold: float = 80.0,
    alert_ram_threshold: float = 85.0,
) -> str:
    """
    Historial de uso de CPU y RAM en el tiempo con detección de picos.
    Útil para responder: "¿Ha habido picos de CPU en la última hora?"
 
    El muestreador se inicia automáticamente al llamar a esta tool por primera vez.
    Usa start_performance_sampler() para controlarlo manualmente.
 
    Args:
        last_n: Número de muestras a devolver (1-1440, una por minuto si sampler activo)
        metric: Qué métricas incluir: "cpu", "ram" o "both"
        alert_cpu_threshold: % CPU que activa una alerta en el historial (0-100)
        alert_ram_threshold: % RAM que activa una alerta en el historial (0-100)
 
    Returns:
        Historial con timestamps, estadísticas (min/max/avg/p95) y alertas detectadas
    """
    logger.info(f"Tool llamada: performance_history(last_n={last_n}, metric={metric})")
    last_n = max(1, min(1440, last_n))
 
    # Auto-iniciar sampler si no está corriendo
    if not start_performance_sampler.__module__:  # siempre True; solo para claridad
        pass
    from tools.performance import _sampler_running
    if not _sampler_running:
        start_performance_sampler(interval_seconds=60)
 
    try:
        data = get_performance_history(
            last_n=last_n,
            metric=metric,  # type: ignore
            alert_cpu_threshold=alert_cpu_threshold,
            alert_ram_threshold=alert_ram_threshold,
        )
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error en performance_history: {e}")
        return json.dumps({"error": str(e)})
 
 
@mcp.tool()
async def manage_performance_sampler(action: str = "status", interval_seconds: int = 60) -> str:
    """
    Controla el muestreador de rendimiento en segundo plano.
 
    Args:
        action: "start", "stop", "clear" o "status"
        interval_seconds: Segundos entre muestras al iniciar (10-3600)
 
    Returns:
        Estado actual del sampler y número de muestras almacenadas
    """
    logger.info(f"Tool llamada: manage_performance_sampler(action={action})")
    from tools.performance import _samples, _sampler_running
 
    if action == "start":
        result = start_performance_sampler(interval_seconds=interval_seconds)
    elif action == "stop":
        result = stop_performance_sampler()
    elif action == "clear":
        result = clear_performance_history()
    elif action == "status":
        result = {
            "running":  _sampler_running,
            "samples":  len(_samples),
            "interval": f"{interval_seconds}s",
        }
    else:
        result = {"error": f"Acción '{action}' no válida. Usa: start, stop, clear, status"}
 
    return json.dumps(result, indent=2, ensure_ascii=False)

# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("System Sentinel MCP Server arrancando...")
    mcp.run(transport="stdio")