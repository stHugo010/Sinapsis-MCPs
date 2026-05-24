"""
tools/hardware.py
Información de hardware: batería, ventiladores, GPU (nvidia/amd) y BIOS.
"""

import subprocess
import shutil
import psutil


def get_hardware_info(
    include_battery: bool = True,
    include_fans: bool = True,
    include_gpu: bool = True,
) -> dict:
    """
    Devuelve información detallada del hardware físico del sistema.
    
    - Batería: nivel, estado de carga, tiempo restante
    - Ventiladores: RPM por sensor (requiere soporte del kernel)
    - GPU: uso, VRAM, temperatura (nvidia-smi o rocm-smi)
    """
    result: dict = {"timestamp": _now()}

    # ── BATERÍA ───────────────────────────────────────────────────────────────
    if include_battery:
        result["battery"] = _get_battery()

    # ── VENTILADORES ─────────────────────────────────────────────────────────
    if include_fans:
        result["fans"] = _get_fans()

    # ── GPU ──────────────────────────────────────────────────────────────────
    if include_gpu:
        result["gpu"] = _get_gpu()

    # ── CPU DETALLADO (complementa health.py) ────────────────────────────────
    result["cpu_detail"] = _get_cpu_detail()

    # ── MEMORIA DETALLADA ────────────────────────────────────────────────────
    result["memory_detail"] = _get_memory_detail()

    return result


# ─── Batería ──────────────────────────────────────────────────────────────────

def _get_battery() -> dict:
    battery = psutil.sensors_battery()
    if battery is None:
        return {"available": False, "note": "No se detectó batería (sistema de escritorio o sin soporte)"}

    secs_left = battery.secsleft
    if secs_left == psutil.POWER_TIME_UNLIMITED:
        time_left = "cargando (AC conectado)"
    elif secs_left == psutil.POWER_TIME_UNKNOWN:
        time_left = "desconocido"
    else:
        h, m = divmod(secs_left // 60, 60)
        time_left = f"{h}h {m}m"

    pct = round(battery.percent, 1)
    return {
        "available":    True,
        "percent":      pct,
        "plugged_in":   battery.power_plugged,
        "time_left":    time_left,
        "status": (
            "charging"  if battery.power_plugged else
            "critical"  if pct < 10 else
            "low"       if pct < 20 else
            "ok"
        ),
    }


# ─── Ventiladores ─────────────────────────────────────────────────────────────

def _get_fans() -> dict:
    try:
        fans_raw = psutil.sensors_fans()
        if not fans_raw:
            return {"available": False, "note": "No se detectaron sensores de ventiladores"}

        fans = {}
        for controller, entries in fans_raw.items():
            fans[controller] = [
                {
                    "label": entry.label or f"fan_{i}",
                    "rpm":   entry.current,
                    "status": (
                        "stopped" if entry.current == 0 else
                        "low"     if entry.current < 500 else
                        "ok"
                    ),
                }
                for i, entry in enumerate(entries)
            ]
        return {"available": True, "controllers": fans}

    except AttributeError:
        return {"available": False, "note": "psutil.sensors_fans() no disponible en este sistema"}


# ─── GPU ──────────────────────────────────────────────────────────────────────

def _get_gpu() -> dict:
    """Intenta nvidia-smi primero, luego rocm-smi, luego /sys para Intel."""

    # ── NVIDIA ────────────────────────────────────────────────────────────────
    if shutil.which("nvidia-smi"):
        try:
            out = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,utilization.gpu,utilization.memory,"
                    "memory.used,memory.total,temperature.gpu,power.draw,driver_version",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True, text=True, timeout=5,
            )
            if out.returncode == 0:
                gpus = []
                for line in out.stdout.strip().splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) < 8:
                        continue
                    name, util_gpu, util_mem, mem_used, mem_total, temp, power, driver = parts
                    gpus.append({
                        "vendor":          "nvidia",
                        "name":            name,
                        "driver":          driver,
                        "util_percent":    _safe_int(util_gpu),
                        "mem_util_percent": _safe_int(util_mem),
                        "mem_used_mb":     _safe_int(mem_used),
                        "mem_total_mb":    _safe_int(mem_total),
                        "temperature_c":   _safe_int(temp),
                        "power_draw_w":    _safe_float(power),
                        "status": _gpu_status(_safe_int(util_gpu), _safe_int(temp)),
                    })
                return {"available": True, "vendor": "nvidia", "gpus": gpus}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # ── AMD ───────────────────────────────────────────────────────────────────
    if shutil.which("rocm-smi"):
        try:
            out = subprocess.run(
                ["rocm-smi", "--showuse", "--showtemp", "--showmeminfo", "vram", "--json"],
                capture_output=True, text=True, timeout=5,
            )
            if out.returncode == 0:
                import json
                data = json.loads(out.stdout)
                gpus = []
                for card, info in data.items():
                    if card == "system":
                        continue
                    gpus.append({
                        "vendor":        "amd",
                        "name":          card,
                        "util_percent":  _safe_float(info.get("GPU use (%)", 0)),
                        "temperature_c": _safe_float(info.get("Temperature (Sensor edge) (C)", 0)),
                        "status": _gpu_status(
                            _safe_float(info.get("GPU use (%)", 0)),
                            _safe_float(info.get("Temperature (Sensor edge) (C)", 0)),
                        ),
                    })
                return {"available": True, "vendor": "amd", "gpus": gpus}
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

    # ── Intel / integrada (básico via /sys) ──────────────────────────────────
    import os
    intel_path = "/sys/class/drm/card0/device/power_usage"
    if os.path.exists(intel_path):
        try:
            with open(intel_path) as f:
                power = f.read().strip()
            return {
                "available": True,
                "vendor":    "intel_integrated",
                "gpus": [{"vendor": "intel", "power_uw": int(power)}],
            }
        except Exception:
            pass

    return {
        "available": False,
        "note": "No se detectó GPU compatible (nvidia-smi / rocm-smi no encontrados)",
    }


# ─── CPU detallado ────────────────────────────────────────────────────────────

def _get_cpu_detail() -> dict:
    """Información de CPU por núcleo y frecuencia por core."""
    per_core_pct = psutil.cpu_percent(interval=0.5, percpu=True)
    per_core_freq = psutil.cpu_freq(percpu=True) or []

    cores = []
    for i, pct in enumerate(per_core_pct):
        core: dict = {"core": i, "usage_percent": pct}
        if i < len(per_core_freq):
            core["freq_mhz"] = round(per_core_freq[i].current, 1)
        cores.append(core)

    # Estadísticas de contexto y interrupciones
    ctx = psutil.cpu_stats()
    return {
        "cores":           cores,
        "ctx_switches":    ctx.ctx_switches,
        "interrupts":      ctx.interrupts,
        "soft_interrupts": ctx.soft_interrupts,
    }


# ─── Memoria detallada ────────────────────────────────────────────────────────

def _get_memory_detail() -> dict:
    """Desglose de memoria: buffers, caché, shared, slab."""
    mem = psutil.virtual_memory()
    detail: dict = {
        "total_gb":     round(mem.total / 1e9, 2),
        "used_gb":      round(mem.used / 1e9, 2),
        "free_gb":      round(mem.free / 1e9, 2),
        "available_gb": round(mem.available / 1e9, 2),
    }
    # Campos opcionales (Linux only)
    for field in ("buffers", "cached", "shared", "slab"):
        val = getattr(mem, field, None)
        if val is not None:
            detail[f"{field}_mb"] = round(val / 1e6, 1)
    return detail


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _gpu_status(util: float, temp: float) -> str:
    if temp >= 85 or util >= 95:
        return "critical"
    if temp >= 75 or util >= 80:
        return "high"
    if util >= 50:
        return "moderate"
    return "ok"

def _safe_int(val, default: int = 0) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def _safe_float(val, default: float = 0.0) -> float:
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return default

def _now() -> str:
    import datetime
    return datetime.datetime.now().isoformat(timespec="seconds")