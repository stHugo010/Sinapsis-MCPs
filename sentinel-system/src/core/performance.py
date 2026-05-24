"""
core/performance.py
Historial de rendimiento con muestreador en segundo plano
"""

import asyncio
import psutil
from collections import deque
from typing import Dict, Any, Deque, Optional
from dataclasses import dataclass, asdict

from ..utils import now_iso
from ..constants import MetricType


@dataclass
class PerformanceSample:
    """Muestra individual de rendimiento"""
    timestamp: str
    cpu_percent: float
    ram_percent: float


# Estado global del sampler
_samples: Deque[PerformanceSample] = deque(maxlen=1440)  # 24 horas a 1min/muestra
_sampler_task: Optional[asyncio.Task] = None
_sampler_running: bool = False
_sampler_interval: int = 60


async def _performance_sampler(interval_seconds: int):
    """Task de muestreo en segundo plano"""
    global _sampler_running
    _sampler_running = True
    
    while _sampler_running:
        try:
            cpu = psutil.cpu_percent(interval=1.0)
            ram = psutil.virtual_memory().percent
            
            sample = PerformanceSample(
                timestamp=now_iso(),
                cpu_percent=round(cpu, 1),
                ram_percent=round(ram, 1),
            )
            
            _samples.append(sample)
            
            await asyncio.sleep(interval_seconds - 1)  # -1 por el interval de cpu_percent
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(interval_seconds)
    
    _sampler_running = False


def start_performance_sampler(interval_seconds: int = 60) -> Dict[str, Any]:
    """
    Inicia el muestreador de rendimiento en segundo plano.
    
    Args:
        interval_seconds: Intervalo entre muestras
    
    Returns:
        Estado del sampler
    """
    global _sampler_task, _sampler_running, _sampler_interval
    
    if _sampler_running:
        return {
            "success": False,
            "message": "El sampler ya está corriendo",
            "interval": _sampler_interval,
        }
    
    _sampler_interval = interval_seconds
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    _sampler_task = loop.create_task(_performance_sampler(interval_seconds))
    
    return {
        "success": True,
        "message": "Sampler iniciado",
        "interval": interval_seconds,
        "samples": len(_samples),
    }


def stop_performance_sampler() -> Dict[str, Any]:
    """Detiene el muestreador"""
    global _sampler_task, _sampler_running
    
    if not _sampler_running:
        return {
            "success": False,
            "message": "El sampler no está corriendo",
        }
    
    _sampler_running = False
    
    if _sampler_task:
        _sampler_task.cancel()
    
    return {
        "success": True,
        "message": "Sampler detenido",
        "samples_collected": len(_samples),
    }


def clear_performance_history() -> Dict[str, Any]:
    """Limpia el historial de muestras"""
    cleared = len(_samples)
    _samples.clear()
    
    return {
        "success": True,
        "message": "Historial limpiado",
        "samples_cleared": cleared,
    }

def get_performance_history(
    last_n: int = 60,
    metric: str = "both",
    alert_cpu_threshold: float = 80.0,
    alert_ram_threshold: float = 85.0,
) -> Dict[str, Any]:
    """
    Obtiene historial de rendimiento con estadísticas y alertas.
    
    Args:
        last_n: Número de muestras a retornar
        metric: Métrica a incluir ("cpu", "ram", "both")
        alert_cpu_threshold: % CPU para alerta
        alert_ram_threshold: % RAM para alerta
    
    Returns:
        Dict con historial y estadísticas
    """
    if not _samples:
        return {
            "error": "No hay muestras disponibles",
            "hint": "El sampler debe estar corriendo. Usa start_performance_sampler()",
            "sampler_running": _sampler_running,
        }
    
    # Tomar últimas N muestras
    samples_list = list(_samples)[-last_n:]
    
    # Extraer datos según métrica solicitada
    cpu_values = [s.cpu_percent for s in samples_list]
    ram_values = [s.ram_percent for s in samples_list]
    
    result: Dict[str, Any] = {
        "timestamp": now_iso(),
        "sampler_running": _sampler_running,
        "total_samples": len(_samples),
        "returned_samples": len(samples_list),
        "metric_filter": metric,
    }
    
    # Estadísticas de CPU
    if metric in [MetricType.CPU, MetricType.BOTH]:
        cpu_sorted = sorted(cpu_values)
        result["cpu_stats"] = {
            "min": round(min(cpu_values), 1),
            "max": round(max(cpu_values), 1),
            "avg": round(sum(cpu_values) / len(cpu_values), 1),
            "p95": round(cpu_sorted[int(len(cpu_sorted) * 0.95)], 1) if cpu_sorted else 0,
        }
        
        # Alertas de CPU
        cpu_alerts = [
            {"timestamp": s.timestamp, "value": s.cpu_percent}
            for s in samples_list
            if s.cpu_percent >= alert_cpu_threshold
        ]
        result["cpu_alerts"] = cpu_alerts
    
    # Estadísticas de RAM
    if metric in [MetricType.RAM, MetricType.BOTH]:
        ram_sorted = sorted(ram_values)
        result["ram_stats"] = {
            "min": round(min(ram_values), 1),
            "max": round(max(ram_values), 1),
            "avg": round(sum(ram_values) / len(ram_values), 1),
            "p95": round(ram_sorted[int(len(ram_sorted) * 0.95)], 1) if ram_sorted else 0,
        }
        
        # Alertas de RAM
        ram_alerts = [
            {"timestamp": s.timestamp, "value": s.ram_percent}
            for s in samples_list
            if s.ram_percent >= alert_ram_threshold
        ]
        result["ram_alerts"] = ram_alerts
    
    # Muestras completas
    result["samples"] = [asdict(s) for s in samples_list]
    
    return result


def get_sampler_status() -> Dict[str, Any]:
    """Obtiene el estado actual del sampler"""
    return {
        "running": _sampler_running,
        "samples": len(_samples),
        "interval": _sampler_interval,
        "max_samples": _samples.maxlen,
    }