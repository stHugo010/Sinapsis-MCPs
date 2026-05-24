"""
server.py
Servidor MCP System Sentinel - Refactorizado

Monitorización y diagnóstico del sistema operativo Linux en tiempo real.

Uso:
    python server.py          # Modo stdio (Claude Desktop)
    python server.py --dev    # Modo debug con logs
    python server.py --sampler # Auto-iniciar sampler de rendimiento
"""

import logging
from mcp.server.fastmcp import FastMCP

from .config import init_config
from .constants import MCP_INSTRUCTIONS
from .core import (
    get_system_health,
    list_processes,
    kill_process,
    ProcessGuardian,
    get_hardware_info,
    get_network_stats,
    analyze_logs,
    start_performance_sampler,
    stop_performance_sampler,
    clear_performance_history,
    get_performance_history,
    get_sampler_status,
)
from .utils import (
    format_json_response,
    format_error,
    format_blocked_operation,
    clamp,
)
from .constants import (
    PROCESS_LIMIT_MIN,
    PROCESS_LIMIT_MAX,
    PROCESS_LIMIT_DEFAULT,
    LOG_LINES_MIN,
    LOG_LINES_MAX,
    LOG_LINES_DEFAULT,
    LOG_TIME_MIN,
    LOG_TIME_MAX,
    HISTORY_SAMPLES_MIN,
    HISTORY_SAMPLES_MAX,
    HISTORY_SAMPLES_DEFAULT,
    PERFORMANCE_INTERVAL_MIN,
    PERFORMANCE_INTERVAL_MAX,
)


# ─── Inicialización ──────────────────────────────────────────────────────────
config = init_config()
logger = config.setup_logging()

# Guardian de seguridad
guardian = ProcessGuardian()

# Servidor MCP
mcp = FastMCP(config.server_name, instructions=MCP_INSTRUCTIONS)


# ─── TOOL 1: System Health ───────────────────────────────────────────────────
@mcp.tool()
async def system_health() -> str:
    """
    Obtiene un snapshot completo del estado del sistema:
    CPU, RAM, disco, swap y temperaturas.
    
    Útil para diagnóstico inicial cuando el sistema va lento.
    
    Returns:
        JSON con métricas del sistema y estados de alerta
    """
    logger.info("Tool: system_health")
    try:
        data = get_system_health()
        return format_json_response(data)
    except Exception as e:
        logger.error(f"Error en system_health: {e}", exc_info=True)
        return format_error(str(e))


# ─── TOOL 2: Top Processes ───────────────────────────────────────────────────
@mcp.tool()
async def top_processes(
    sort_by: str = "cpu",
    limit: int = PROCESS_LIMIT_DEFAULT,
    include_system: bool = False,
) -> str:
    """
    Lista los procesos que más recursos consumen.
    
    Args:
        sort_by: Criterio de ordenación. Opciones: "cpu", "memory", "io"
        limit: Número máximo de procesos (1-50)
        include_system: Si True, incluye procesos del sistema/kernel
    
    Returns:
        JSON con lista de procesos y metadata
    """
    logger.info(f"Tool: top_processes(sort_by={sort_by}, limit={limit})")
    
    # Validar límites
    limit = int(clamp(limit, PROCESS_LIMIT_MIN, PROCESS_LIMIT_MAX))
    
    try:
        data = list_processes(sort_by=sort_by, limit=limit, include_system=include_system)
        return format_json_response(data)
    except Exception as e:
        logger.error(f"Error en top_processes: {e}", exc_info=True)
        return format_error(str(e))


# ─── TOOL 3: Terminate Process ───────────────────────────────────────────────
@mcp.tool()
async def terminate_process(
    pid: int,
    force: bool = False,
    reason: str = "",
) -> str:
    """
    Termina un proceso del sistema por su PID.
    
    ⚠️  IMPORTANTE: Esta herramienta tiene impacto real en el sistema.
    Úsala solo cuando el usuario haya confirmado explícitamente.
    
    Args:
        pid: ID del proceso a terminar (obligatorio)
        force: Si True, usa SIGKILL (forzado). Si False, usa SIGTERM (graceful)
        reason: Razón de terminación (para auditoría)
    
    Returns:
        JSON con resultado de la operación
    """
    logger.info(f"Tool: terminate_process(pid={pid}, force={force})")
    
    # Verificación de seguridad ANTES de actuar
    if config.enable_guardian:
        check = guardian.is_safe_to_kill(pid)
        if not check["safe"]:
            logger.warning(f"Guardian bloqueó terminación de PID {pid}: {check['reason']}")
            return format_blocked_operation(check["reason"])
    
    try:
        result = kill_process(pid=pid, force=force)
        
        # Auditoría
        if result.get("success"):
            logger.warning(
                f"AUDITORÍA: Proceso terminado | PID={pid} | "
                f"Nombre={result.get('process', {}).get('name', 'unknown')} | "
                f"Force={force} | Razón='{reason}'"
            )
        
        return format_json_response(result)
    except Exception as e:
        logger.error(f"Error en terminate_process: {e}", exc_info=True)
        return format_json_response({"success": False, "error": str(e)})

# ─── TOOL 4: System Logs ─────────────────────────────────────────────────────
@mcp.tool()
async def read_system_logs(
    lines: int = LOG_LINES_DEFAULT,
    level: str = "error",
    since_minutes: int = 60,
) -> str:
    """
    Lee y filtra los logs del sistema (journalctl / syslog).
    
    Args:
        lines: Número máximo de líneas (10-500)
        level: Nivel mínimo. Opciones: "error", "warning", "info", "all"
        since_minutes: Analizar logs de los últimos N minutos (1-1440)
    
    Returns:
        JSON con entradas de log filtradas
    
    Nota: Puede requerir permisos de root para ciertos logs.
    """
    logger.info(f"Tool: read_system_logs(lines={lines}, level={level})")
    
    # Validar límites
    lines = int(clamp(lines, LOG_LINES_MIN, LOG_LINES_MAX))
    since_minutes = int(clamp(since_minutes, LOG_TIME_MIN, LOG_TIME_MAX))
    
    try:
        data = analyze_logs(lines=lines, level=level, since_minutes=since_minutes)
        return format_json_response(data)
    except PermissionError:
        return format_error(
            "Permisos insuficientes",
            "Ejecuta el servidor MCP con sudo para acceder a logs del sistema"
        )
    except Exception as e:
        logger.error(f"Error en read_system_logs: {e}", exc_info=True)
        return format_error(str(e))


# ─── TOOL 5: Network Connections ─────────────────────────────────────────────
@mcp.tool()
async def network_connections(
    show_listening: bool = True,
    show_established: bool = True,
    flag_external: bool = True,
) -> str:
    """
    Muestra conexiones de red activas y estadísticas de tráfico.
    
    Útil para detectar procesos sospechosos conectados a IPs externas.
    
    Args:
        show_listening: Incluir puertos en escucha
        show_established: Incluir conexiones establecidas
        flag_external: Marcar conexiones a IPs externas
    
    Returns:
        JSON con conexiones y estadísticas de red
    """
    logger.info("Tool: network_connections")
    try:
        data = get_network_stats(
            show_listening=show_listening,
            show_established=show_established,
            flag_external=flag_external,
        )
        return format_json_response(data)
    except Exception as e:
        logger.error(f"Error en network_connections: {e}", exc_info=True)
        return format_error(str(e))


# ─── TOOL 6: Hardware Info ───────────────────────────────────────────────────
@mcp.tool()
async def hardware_info(
    include_battery: bool = True,
    include_fans: bool = True,
    include_gpu: bool = True,
) -> str:
    """
    Información detallada del hardware: batería, ventiladores, GPU y memoria.
    
    Detecta automáticamente NVIDIA (nvidia-smi), AMD (rocm-smi) e Intel.
    
    Args:
        include_battery: Incluir estado de batería
        include_fans: Incluir RPM de ventiladores
        include_gpu: Incluir GPU (uso, temperatura, VRAM)
    
    Returns:
        JSON con snapshot de hardware
    """
    logger.info("Tool: hardware_info")
    try:
        data = get_hardware_info(
            include_battery=include_battery,
            include_fans=include_fans,
            include_gpu=include_gpu,
        )
        return format_json_response(data)
    except Exception as e:
        logger.error(f"Error en hardware_info: {e}", exc_info=True)
        return format_error(str(e))

# ─── TOOL 7: Performance History ─────────────────────────────────────────────
@mcp.tool()
async def performance_history(
    last_n: int = HISTORY_SAMPLES_DEFAULT,
    metric: str = "both",
    alert_cpu_threshold: float = 80.0,
    alert_ram_threshold: float = 85.0,
) -> str:
    """
    Historial de uso de CPU y RAM con detección de picos.
    
    El sampler se auto-inicia en la primera llamada si no está corriendo.
    
    Args:
        last_n: Número de muestras a retornar (1-1440)
        metric: Métricas a incluir: "cpu", "ram" o "both"
        alert_cpu_threshold: % CPU para alertas (0-100)
        alert_ram_threshold: % RAM para alertas (0-100)
    
    Returns:
        JSON con historial, estadísticas y alertas
    """
    logger.info(f"Tool: performance_history(last_n={last_n}, metric={metric})")
    
    # Validar límites
    last_n = int(clamp(last_n, HISTORY_SAMPLES_MIN, HISTORY_SAMPLES_MAX))
    
    # Auto-iniciar sampler si no está corriendo
    status = get_sampler_status()
    if not status["running"]:
        logger.info("Auto-iniciando performance sampler...")
        start_performance_sampler(interval_seconds=60)
    
    try:
        data = get_performance_history(
            last_n=last_n,
            metric=metric,
            alert_cpu_threshold=alert_cpu_threshold,
            alert_ram_threshold=alert_ram_threshold,
        )
        return format_json_response(data)
    except Exception as e:
        logger.error(f"Error en performance_history: {e}", exc_info=True)
        return format_error(str(e))


# ─── TOOL 8: Manage Performance Sampler ──────────────────────────────────────
@mcp.tool()
async def manage_performance_sampler(
    action: str = "status",
    interval_seconds: int = 60,
) -> str:
    """
    Controla el muestreador de rendimiento en segundo plano.
    
    Args:
        action: "start", "stop", "clear" o "status"
        interval_seconds: Segundos entre muestras (10-3600)
    
    Returns:
        JSON con estado del sampler
    """
    logger.info(f"Tool: manage_performance_sampler(action={action})")
    
    # Validar intervalo
    interval_seconds = int(clamp(interval_seconds, PERFORMANCE_INTERVAL_MIN, PERFORMANCE_INTERVAL_MAX))
    
    try:
        if action == "start":
            result = start_performance_sampler(interval_seconds=interval_seconds)
        elif action == "stop":
            result = stop_performance_sampler()
        elif action == "clear":
            result = clear_performance_history()
        elif action == "status":
            result = get_sampler_status()
        else:
            result = {
                "error": f"Acción '{action}' no válida",
                "hint": "Usa: start, stop, clear, status",
            }
        
        return format_json_response(result)
    except Exception as e:
        logger.error(f"Error en manage_performance_sampler: {e}", exc_info=True)
        return format_error(str(e))


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("System Sentinel MCP Server iniciando...")
    
    # Auto-iniciar sampler si está configurado
    if config.sampler_enabled:
        logger.info("Iniciando performance sampler automáticamente...")
        start_performance_sampler(interval_seconds=config.sampler_interval)
    
    mcp.run(transport=config.transport)