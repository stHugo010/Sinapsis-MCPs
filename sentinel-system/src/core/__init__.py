"""
core package
Lógica de negocio del sistema de monitorización
"""

from .health import get_system_health
from .processes import list_processes, kill_process, get_process_info
from .guardian import ProcessGuardian
from .hardware import get_hardware_info, get_battery_info, get_gpu_info, get_fans_info
from .network import get_network_stats
from .logs import analyze_logs
from .performance import (
    start_performance_sampler,
    stop_performance_sampler,
    clear_performance_history,
    get_performance_history,
    get_sampler_status,
)

__all__ = [
    "get_system_health",
    "list_processes",
    "kill_process",
    "get_process_info",
    "ProcessGuardian",
    "get_hardware_info",
    "get_battery_info",
    "get_gpu_info",
    "get_fans_info",
    "get_network_stats",
    "analyze_logs",
    "start_performance_sampler",
    "stop_performance_sampler",
    "clear_performance_history",
    "get_performance_history",
    "get_sampler_status",
]