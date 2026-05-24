"""
core/hardware.py
Información de hardware: batería, GPU, ventiladores, CPU y memoria detallada
"""

import subprocess
import shutil
import psutil
from typing import Dict, Any, Optional

from ..utils import now_iso, safe_int, safe_float, bytes_to_gb, bytes_to_mb, format_time_left
from ..constants import (
    GPU_UTIL_HIGH,
    GPU_UTIL_CRITICAL,
    GPU_TEMP_HIGH,
    GPU_TEMP_CRITICAL,
    BATTERY_LOW,
    BATTERY_CRITICAL,
    SystemStatus,
)


def get_hardware_info(
    include_battery: bool = True,
    include_fans: bool = True,
    include_gpu: bool = True,
) -> Dict[str, Any]:
    """
    Obtiene información detallada del hardware físico.
    
    Args:
        include_battery: Incluir estado de batería
        include_fans: Incluir ventiladores
        include_gpu: Incluir GPU
    
    Returns:
        Dict con información de hardware
    """
    result: Dict[str, Any] = {"timestamp": now_iso()}
    
    if include_battery:
        result["battery"] = get_battery_info()
    
    if include_fans:
        result["fans"] = get_fans_info()
    
    if include_gpu:
        result["gpu"] = get_gpu_info()
    
    result["cpu_detail"] = get_cpu_detail()
    result["memory_detail"] = get_memory_detail()
    
    return result


def get_battery_info() -> Dict[str, Any]:
    """Obtiene información de batería"""
    battery = psutil.sensors_battery()
    
    if battery is None:
        return {
            "available": False,
            "note": "No se detectó batería (sistema de escritorio o sin soporte)",
        }
    
    # Calcular tiempo restante
    secs_left = battery.secsleft
    if secs_left == psutil.POWER_TIME_UNLIMITED:
        time_left = "cargando (AC conectado)"
    elif secs_left == psutil.POWER_TIME_UNKNOWN:
        time_left = "desconocido"
    else:
        time_left = format_time_left(secs_left)
    
    percent = round(battery.percent, 1)
    
    # Determinar estado
    if battery.power_plugged:
        status = SystemStatus.OK
    elif percent < BATTERY_CRITICAL:
        status = SystemStatus.CRITICAL
    elif percent < BATTERY_LOW:
        status = SystemStatus.WARNING
    else:
        status = SystemStatus.OK
    
    return {
        "available": True,
        "percent": percent,
        "plugged_in": battery.power_plugged,
        "time_left": time_left,
        "status": status,
    }


def get_fans_info() -> Dict[str, Any]:
    """Obtiene información de ventiladores"""
    try:
        fans_raw = psutil.sensors_fans()
        if not fans_raw:
            return {
                "available": False,
                "note": "No se detectaron sensores de ventiladores",
            }
        
        fans = {}
        for controller, entries in fans_raw.items():
            fans[controller] = [
                {
                    "label": entry.label or f"fan_{i}",
                    "rpm": entry.current,
                    "status": (
                        "stopped" if entry.current == 0 else
                        "low" if entry.current < 500 else
                        "ok"
                    ),
                }
                for i, entry in enumerate(entries)
            ]
        
        return {
            "available": True,
            "controllers": fans,
        }
    
    except AttributeError:
        return {
            "available": False,
            "note": "psutil.sensors_fans() no disponible en este sistema",
        }


def get_gpu_info() -> Dict[str, Any]:
    """
    Detecta y obtiene información de GPU (NVIDIA, AMD o Intel).
    Prioridad: NVIDIA > AMD > Intel
    """
    # Intentar NVIDIA
    nvidia_info = _get_nvidia_gpu()
    if nvidia_info["available"]:
        return nvidia_info
    
    # Intentar AMD
    amd_info = _get_amd_gpu()
    if amd_info["available"]:
        return amd_info
    
    # Intentar Intel integrada
    intel_info = _get_intel_gpu()
    if intel_info["available"]:
        return intel_info
    
    return {
        "available": False,
        "note": "No se detectó GPU compatible (nvidia-smi / rocm-smi no encontrados)",
    }


def _get_nvidia_gpu() -> Dict[str, Any]:
    """Obtiene información de GPU NVIDIA"""
    if not shutil.which("nvidia-smi"):
        return {"available": False}
    
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,utilization.memory,"
                "memory.used,memory.total,temperature.gpu,power.draw,driver_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        
        if result.returncode != 0:
            return {"available": False}
        
        gpus = []
        for line in result.stdout.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 8:
                continue
            
            name, util_gpu, util_mem, mem_used, mem_total, temp, power, driver = parts
            
            util_val = safe_int(util_gpu)
            temp_val = safe_int(temp)
            
            gpus.append({
                "vendor": "nvidia",
                "name": name,
                "driver": driver,
                "util_percent": util_val,
                "mem_util_percent": safe_int(util_mem),
                "mem_used_mb": safe_int(mem_used),
                "mem_total_mb": safe_int(mem_total),
                "temperature_c": temp_val,
                "power_draw_w": safe_float(power),
                "status": _gpu_status(util_val, temp_val),
            })
        
        return {
            "available": True,
            "vendor": "nvidia",
            "gpus": gpus,
        }
    
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return {"available": False}

def _get_amd_gpu() -> Dict[str, Any]:
    """Obtiene información de GPU AMD"""
    if not shutil.which("rocm-smi"):
        return {"available": False}
    
    try:
        result = subprocess.run(
            ["rocm-smi", "--showuse", "--showtemp", "--showmeminfo", "vram", "--json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        
        if result.returncode != 0:
            return {"available": False}
        
        import json
        data = json.loads(result.stdout)
        
        gpus = []
        for card, info in data.items():
            if card == "system":
                continue
            
            util_val = safe_float(info.get("GPU use (%)", 0))
            temp_val = safe_float(info.get("Temperature (Sensor edge) (C)", 0))
            
            gpus.append({
                "vendor": "amd",
                "name": card,
                "util_percent": util_val,
                "temperature_c": temp_val,
                "status": _gpu_status(util_val, temp_val),
            })
        
        return {
            "available": True,
            "vendor": "amd",
            "gpus": gpus,
        }
    
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return {"available": False}


def _get_intel_gpu() -> Dict[str, Any]:
    """Obtiene información básica de GPU Intel integrada"""
    import os
    intel_path = "/sys/class/drm/card0/device/power_usage"
    
    if not os.path.exists(intel_path):
        return {"available": False}
    
    try:
        with open(intel_path) as f:
            power_uw = int(f.read().strip())
        
        return {
            "available": True,
            "vendor": "intel_integrated",
            "gpus": [{
                "vendor": "intel",
                "power_uw": power_uw,
                "status": SystemStatus.OK,
            }],
        }
    except Exception:
        return {"available": False}


def _gpu_status(utilization: float, temperature: float) -> str:
    """Determina el estado de una GPU basado en uso y temperatura"""
    if temperature >= GPU_TEMP_CRITICAL or utilization >= GPU_UTIL_CRITICAL:
        return SystemStatus.CRITICAL
    if temperature >= GPU_TEMP_HIGH or utilization >= GPU_UTIL_HIGH:
        return SystemStatus.WARNING
    if utilization >= 50:
        return "moderate"
    return SystemStatus.OK


def get_cpu_detail() -> Dict[str, Any]:
    """Obtiene información detallada de CPU por núcleo"""
    per_core_pct = psutil.cpu_percent(interval=0.5, percpu=True)
    per_core_freq = psutil.cpu_freq(percpu=True) or []
    
    cores = []
    for i, pct in enumerate(per_core_pct):
        core: Dict[str, Any] = {
            "core": i,
            "usage_percent": round(pct, 1),
        }
        if i < len(per_core_freq):
            core["freq_mhz"] = round(per_core_freq[i].current, 1)
        cores.append(core)
    
    # Estadísticas de sistema
    stats = psutil.cpu_stats()
    
    return {
        "cores": cores,
        "ctx_switches": stats.ctx_switches,
        "interrupts": stats.interrupts,
        "soft_interrupts": stats.soft_interrupts,
    }


def get_memory_detail() -> Dict[str, Any]:
    """Obtiene desglose detallado de memoria"""
    mem = psutil.virtual_memory()
    
    detail: Dict[str, Any] = {
        "total_gb": bytes_to_gb(mem.total),
        "used_gb": bytes_to_gb(mem.used),
        "free_gb": bytes_to_gb(mem.free),
        "available_gb": bytes_to_gb(mem.available),
        "usage_percent": round(mem.percent, 1),
    }
    
    # Campos opcionales (solo Linux)
    for field in ("buffers", "cached", "shared", "slab"):
        val = getattr(mem, field, None)
        if val is not None:
            detail[f"{field}_mb"] = bytes_to_mb(val)
    
    return detail