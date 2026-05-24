"""
core/health.py
Lógica de negocio para monitorización de salud del sistema
"""

import psutil
from typing import Dict, Any

from ..utils import now_iso, bytes_to_gb, safe_float
from ..constants import (
    CPU_ALERT_THRESHOLD,
    RAM_ALERT_THRESHOLD,
    DISK_ALERT_THRESHOLD,
    TEMP_WARNING_THRESHOLD,
    TEMP_CRITICAL_THRESHOLD,
    SystemStatus,
)


def get_system_health() -> Dict[str, Any]:
    """
    Obtiene snapshot completo del estado del sistema.
    
    Returns:
        Dict con CPU, RAM, disco, swap y temperaturas
    """
    return {
        "timestamp": now_iso(),
        "cpu": _get_cpu_info(),
        "memory": _get_memory_info(),
        "disk": _get_disk_info(),
        "swap": _get_swap_info(),
        "temperatures": _get_temperature_info(),
        "system_status": _calculate_system_status(),
    }


def _get_cpu_info() -> Dict[str, Any]:
    """Información de CPU"""
    cpu_percent = psutil.cpu_percent(interval=1.0)
    cpu_freq = psutil.cpu_freq()
    cpu_count = psutil.cpu_count(logical=True)
    cpu_count_physical = psutil.cpu_count(logical=False) or cpu_count
    
    status = SystemStatus.OK
    if cpu_percent >= 95:
        status = SystemStatus.CRITICAL
    elif cpu_percent >= CPU_ALERT_THRESHOLD:
        status = SystemStatus.WARNING
    
    info: Dict[str, Any] = {
        "usage_percent": round(cpu_percent, 1),
        "cores_logical": cpu_count,
        "cores_physical": cpu_count_physical,
        "status": status,
    }
    
    if cpu_freq:
        info["frequency_mhz"] = {
            "current": round(cpu_freq.current, 1),
            "min": round(cpu_freq.min, 1),
            "max": round(cpu_freq.max, 1),
        }
    
    return info


def _get_memory_info() -> Dict[str, Any]:
    """Información de memoria RAM"""
    mem = psutil.virtual_memory()
    
    status = SystemStatus.OK
    if mem.percent >= 95:
        status = SystemStatus.CRITICAL
    elif mem.percent >= RAM_ALERT_THRESHOLD:
        status = SystemStatus.WARNING
    
    return {
        "total_gb": bytes_to_gb(mem.total),
        "used_gb": bytes_to_gb(mem.used),
        "available_gb": bytes_to_gb(mem.available),
        "usage_percent": round(mem.percent, 1),
        "status": status,
    }


def _get_disk_info() -> Dict[str, Any]:
    """Información de disco principal"""
    disk = psutil.disk_usage("/")
    
    status = SystemStatus.OK
    if disk.percent >= 98:
        status = SystemStatus.CRITICAL
    elif disk.percent >= DISK_ALERT_THRESHOLD:
        status = SystemStatus.WARNING
    
    return {
        "total_gb": bytes_to_gb(disk.total),
        "used_gb": bytes_to_gb(disk.used),
        "free_gb": bytes_to_gb(disk.free),
        "usage_percent": round(disk.percent, 1),
        "status": status,
    }


def _get_swap_info() -> Dict[str, Any]:
    """Información de memoria swap"""
    swap = psutil.swap_memory()
    
    if swap.total == 0:
        return {
            "enabled": False,
            "note": "Swap no configurado",
        }
    
    status = SystemStatus.OK
    if swap.percent >= 80:
        status = SystemStatus.WARNING
    
    return {
        "enabled": True,
        "total_gb": bytes_to_gb(swap.total),
        "used_gb": bytes_to_gb(swap.used),
        "free_gb": bytes_to_gb(swap.free),
        "usage_percent": round(swap.percent, 1),
        "status": status,
    }


def _get_temperature_info() -> Dict[str, Any]:
    """Información de temperaturas del sistema"""
    try:
        temps_raw = psutil.sensors_temperatures()
        if not temps_raw:
            return {
                "available": False,
                "note": "Sensores de temperatura no disponibles",
            }
        
        temps: Dict[str, Any] = {"available": True, "sensors": {}}
        max_temp = 0.0
        
        for device, entries in temps_raw.items():
            device_temps = []
            for entry in entries:
                temp = safe_float(entry.current)
                if temp > max_temp:
                    max_temp = temp
                
                temp_status = SystemStatus.OK
                if temp >= TEMP_CRITICAL_THRESHOLD:
                    temp_status = SystemStatus.CRITICAL
                elif temp >= TEMP_WARNING_THRESHOLD:
                    temp_status = SystemStatus.WARNING
                
                device_temps.append({
                    "label": entry.label or "unknown",
                    "current_c": temp,
                    "high_c": safe_float(entry.high) if entry.high else None,
                    "critical_c": safe_float(entry.critical) if entry.critical else None,
                    "status": temp_status,
                })
            
            temps["sensors"][device] = device_temps
        
        # Estado general de temperatura
        overall_status = SystemStatus.OK
        if max_temp >= TEMP_CRITICAL_THRESHOLD:
            overall_status = SystemStatus.CRITICAL
        elif max_temp >= TEMP_WARNING_THRESHOLD:
            overall_status = SystemStatus.WARNING
        
        temps["max_temperature_c"] = max_temp
        temps["status"] = overall_status
        
        return temps
        
    except AttributeError:
        return {
            "available": False,
            "note": "psutil.sensors_temperatures() no disponible en este sistema",
        }


def _calculate_system_status() -> str:
    """Calcula el estado general del sistema"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage("/").percent
    
    # Crítico si algún recurso está al límite
    if cpu_percent >= 95 or mem_percent >= 95 or disk_percent >= 98:
        return SystemStatus.CRITICAL
    
    # Warning si algún recurso está alto
    if cpu_percent >= CPU_ALERT_THRESHOLD or \
       mem_percent >= RAM_ALERT_THRESHOLD or \
       disk_percent >= DISK_ALERT_THRESHOLD:
        return SystemStatus.WARNING
    
    return SystemStatus.OK