"""
tools/health.py
Obtiene el estado de salud del sistema: CPU, RAM, disco, swap y temperaturas.
"""

import datetime
import psutil


def get_system_health() -> dict:
    """
    Retorna un snapshot completo del estado del sistema.
    Todos los porcentajes son 0-100. Temperaturas en °C.
    """
    now = datetime.datetime.now().isoformat(timespec="seconds")

    # ── CPU ──────────────────────────────────────────────────────────────────
    cpu_percent = psutil.cpu_percent(interval=1)          # 1s de muestreo para precisión
    cpu_freq    = psutil.cpu_freq()
    cpu_count   = psutil.cpu_count(logical=True)
    cpu_count_physical = psutil.cpu_count(logical=False)
    load_avg    = psutil.getloadavg()                      # (1m, 5m, 15m)

    cpu_info = {
        "usage_percent": cpu_percent,
        "logical_cores": cpu_count,
        "physical_cores": cpu_count_physical,
        "load_avg_1m": round(load_avg[0], 2),
        "load_avg_5m": round(load_avg[1], 2),
        "load_avg_15m": round(load_avg[2], 2),
    }
    if cpu_freq:
        cpu_info["freq_current_mhz"] = round(cpu_freq.current, 1)
        cpu_info["freq_max_mhz"]     = round(cpu_freq.max, 1)

    # Estado semántico del CPU
    if cpu_percent < 50:
        cpu_info["status"] = "ok"
    elif cpu_percent < 80:
        cpu_info["status"] = "moderate"
    else:
        cpu_info["status"] = "high"

    # ── RAM ──────────────────────────────────────────────────────────────────
    mem = psutil.virtual_memory()
    ram_info = {
        "total_gb":     round(mem.total / 1e9, 2),
        "used_gb":      round(mem.used / 1e9, 2),
        "available_gb": round(mem.available / 1e9, 2),
        "usage_percent": mem.percent,
        "status": "ok" if mem.percent < 70 else ("moderate" if mem.percent < 90 else "critical"),
    }

    # ── SWAP ─────────────────────────────────────────────────────────────────
    swap = psutil.swap_memory()
    swap_info = {
        "total_gb":     round(swap.total / 1e9, 2),
        "used_gb":      round(swap.used / 1e9, 2),
        "usage_percent": swap.percent,
        "status": "ok" if swap.percent < 50 else ("moderate" if swap.percent < 80 else "high"),
    }

    # ── DISCO ─────────────────────────────────────────────────────────────────
    disks = []
    for part in psutil.disk_partitions(all=False):
        # Saltamos pseudo-filesystems (tmpfs, devtmpfs, etc.)
        if part.fstype in ("tmpfs", "devtmpfs", "squashfs", ""):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "mountpoint":    part.mountpoint,
                "device":        part.device,
                "fstype":        part.fstype,
                "total_gb":      round(usage.total / 1e9, 2),
                "used_gb":       round(usage.used / 1e9, 2),
                "free_gb":       round(usage.free / 1e9, 2),
                "usage_percent": usage.percent,
                "status": "ok" if usage.percent < 75 else ("warning" if usage.percent < 90 else "critical"),
            })
        except PermissionError:
            continue

    # ── TEMPERATURAS ─────────────────────────────────────────────────────────
    temperatures = {}
    try:
        temps = psutil.sensors_temperatures()
        for sensor_name, entries in temps.items():
            temperatures[sensor_name] = [
                {
                    "label":   entry.label or "core",
                    "current": entry.current,
                    "high":    entry.high,
                    "critical": entry.critical,
                    "status": _temp_status(entry.current, entry.high, entry.critical),
                }
                for entry in entries
            ]
    except AttributeError:
        temperatures = {"note": "Sensores de temperatura no disponibles en este sistema"}

    # ── UPTIME ────────────────────────────────────────────────────────────────
    boot_time = psutil.boot_time()
    uptime_seconds = datetime.datetime.now().timestamp() - boot_time
    uptime_str = _format_uptime(uptime_seconds)

    # ── RESUMEN GLOBAL ────────────────────────────────────────────────────────
    all_statuses = [
        cpu_info["status"],
        ram_info["status"],
        swap_info["status"],
        *(d["status"] for d in disks),
    ]
    if "critical" in all_statuses:
        overall = "critical"
    elif "high" in all_statuses or "warning" in all_statuses:
        overall = "warning"
    elif "moderate" in all_statuses:
        overall = "moderate"
    else:
        overall = "healthy"

    return {
        "timestamp":    now,
        "overall_status": overall,
        "uptime":       uptime_str,
        "cpu":          cpu_info,
        "ram":          ram_info,
        "swap":         swap_info,
        "disks":        disks,
        "temperatures": temperatures,
    }


def _temp_status(current: float, high: float | None, critical: float | None) -> str:
    if critical and current >= critical:
        return "critical"
    if high and current >= high:
        return "high"
    if current >= 70:
        return "warm"
    return "ok"


def _format_uptime(seconds: float) -> str:
    days    = int(seconds // 86400)
    hours   = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"