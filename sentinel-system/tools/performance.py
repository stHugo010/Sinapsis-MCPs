"""
tools/performance.py
Historial de rendimiento: muestreo de CPU/RAM en el tiempo y alertas por umbral.

Usa un buffer circular en memoria (no persiste entre reinicios del servidor).
Para persistencia real, se podría integrar con SQLite o InfluxDB.
"""

import datetime
import time
import threading
import psutil
from collections import deque
from typing import Literal


# ─── Buffer circular global (compartido entre tools) ─────────────────────────
# Máximo 1440 muestras = 24h si se muestrea cada minuto
_MAX_SAMPLES = 1440
_samples: deque[dict] = deque(maxlen=_MAX_SAMPLES)
_sampler_thread: threading.Thread | None = None
_sampler_running = False
_sampler_interval = 60  # segundos entre muestras


def get_performance_history(
    last_n: int = 60,
    metric: Literal["cpu", "ram", "both"] = "both",
    alert_cpu_threshold: float = 80.0,
    alert_ram_threshold: float = 85.0,
) -> dict:
    """
    Devuelve el historial de uso de CPU y RAM muestreado en el tiempo.
    Incluye detección de picos y alertas si se superan los umbrales.

    Args:
        last_n: Número de muestras a devolver (máx 1440)
        metric: Qué métrica incluir: "cpu", "ram" o "both"
        alert_cpu_threshold: % de CPU que activa una alerta (0-100)
        alert_ram_threshold: % de RAM que activa una alerta (0-100)

    Returns:
        Historial con timestamps, valores, estadísticas y alertas detectadas
    """
    last_n = max(1, min(_MAX_SAMPLES, last_n))

    # Si no hay muestras aún, tomar una instantánea ahora
    if not _samples:
        _take_sample()

    recent = list(_samples)[-last_n:]

    history_cpu = []
    history_ram = []
    alerts = []

    for s in recent:
        ts = s["timestamp"]
        if metric in ("cpu", "both"):
            history_cpu.append({"t": ts, "v": s["cpu_percent"]})
            if s["cpu_percent"] >= alert_cpu_threshold:
                alerts.append({
                    "timestamp": ts,
                    "metric":    "cpu",
                    "value":     s["cpu_percent"],
                    "threshold": alert_cpu_threshold,
                    "message":   f"CPU al {s['cpu_percent']}% (umbral: {alert_cpu_threshold}%)",
                })

        if metric in ("ram", "both"):
            history_ram.append({"t": ts, "v": s["ram_percent"]})
            if s["ram_percent"] >= alert_ram_threshold:
                alerts.append({
                    "timestamp": ts,
                    "metric":    "ram",
                    "value":     s["ram_percent"],
                    "threshold": alert_ram_threshold,
                    "message":   f"RAM al {s['ram_percent']}% (umbral: {alert_ram_threshold}%)",
                })

    result: dict = {
        "sampler_active":   _sampler_running,
        "sampler_interval": f"cada {_sampler_interval}s",
        "total_stored":     len(_samples),
        "showing":          len(recent),
        "alerts":           alerts,
        "alert_count":      len(alerts),
    }

    if metric in ("cpu", "both") and history_cpu:
        vals = [p["v"] for p in history_cpu]
        result["cpu"] = {
            "history":  history_cpu,
            "stats":    _stats(vals),
        }

    if metric in ("ram", "both") and history_ram:
        vals = [p["v"] for p in history_ram]
        result["ram"] = {
            "history":  history_ram,
            "stats":    _stats(vals),
        }

    return result


def start_performance_sampler(interval_seconds: int = 60) -> dict:
    """
    Inicia el muestreador de rendimiento en segundo plano.
    Recoge CPU y RAM automáticamente cada N segundos.

    Args:
        interval_seconds: Segundos entre muestras (10-3600)

    Returns:
        Estado del sampler
    """
    global _sampler_thread, _sampler_running, _sampler_interval

    interval_seconds = max(10, min(3600, interval_seconds))
    _sampler_interval = interval_seconds

    if _sampler_running and _sampler_thread and _sampler_thread.is_alive():
        return {
            "status":   "already_running",
            "interval": f"{interval_seconds}s",
            "samples":  len(_samples),
        }

    _sampler_running = True

    def _loop():
        while _sampler_running:
            _take_sample()
            time.sleep(_sampler_interval)

    _sampler_thread = threading.Thread(target=_loop, daemon=True, name="perf-sampler")
    _sampler_thread.start()

    return {
        "status":   "started",
        "interval": f"{interval_seconds}s",
        "message":  f"Muestreador iniciado. Recogerá datos cada {interval_seconds}s en segundo plano.",
    }


def stop_performance_sampler() -> dict:
    """Detiene el muestreador de rendimiento en segundo plano."""
    global _sampler_running
    _sampler_running = False
    return {
        "status":  "stopped",
        "samples_collected": len(_samples),
    }


def clear_performance_history() -> dict:
    """Limpia el buffer de historial de rendimiento."""
    _samples.clear()
    return {"status": "cleared", "message": "Historial de rendimiento borrado"}


# ─── Helpers internos ─────────────────────────────────────────────────────────

def _take_sample() -> None:
    """Toma una muestra de CPU y RAM y la añade al buffer."""
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        _samples.append({
            "timestamp":   datetime.datetime.now().isoformat(timespec="seconds"),
            "cpu_percent": round(cpu, 1),
            "ram_percent": round(mem.percent, 1),
            "ram_used_gb": round(mem.used / 1e9, 2),
            "swap_percent": round(swap.percent, 1),
        })
    except Exception:
        pass  # Silencioso: el sampler no debe romper el servidor


def _stats(values: list[float]) -> dict:
    """Estadísticas descriptivas básicas de una serie de valores."""
    if not values:
        return {}
    n = len(values)
    avg = sum(values) / n
    sorted_v = sorted(values)
    p95 = sorted_v[int(n * 0.95)]
    return {
        "min":   round(min(values), 1),
        "max":   round(max(values), 1),
        "avg":   round(avg, 1),
        "p95":   round(p95, 1),         # Percentil 95: útil para ver picos
        "count": n,
    }