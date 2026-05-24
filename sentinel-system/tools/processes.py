"""
tools/processes.py
Listado y terminación de procesos del sistema.
"""

import os
import signal
import psutil
from typing import Literal


# Campos que extraemos de cada proceso (whitelist explícita → no filtramos datos sensibles)
_SAFE_FIELDS = {"pid", "name", "username", "status", "cpu_percent", "memory_percent",
                "num_threads", "create_time", "exe", "cmdline"}


def list_processes(
    sort_by: Literal["cpu", "memory", "io"] = "cpu",
    limit: int = 10,
    include_system: bool = False,
) -> dict:
    """
    Devuelve los procesos ordenados por consumo de recursos.
    
    Incluye una primera pasada de cpu_percent(interval=None) y luego
    espera 0.1s para que psutil tenga muestras válidas.
    """
    import time

    # Primera pasada para inicializar los contadores de CPU
    for proc in psutil.process_iter(["pid", "cpu_percent"]):
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    time.sleep(0.5)  # Espera mínima para que los valores sean representativos

    processes = []
    for proc in psutil.process_iter(["pid", "name", "username", "status",
                                     "cpu_percent", "memory_percent",
                                     "num_threads", "exe"]):
        try:
            info = proc.as_dict(attrs=["pid", "name", "username", "status",
                                       "cpu_percent", "memory_percent",
                                       "num_threads", "exe"])
            
            # Filtrar procesos del sistema si no se solicitan
            if not include_system and _is_system_process(info):
                continue

            # Sanitización: cmdline puede contener rutas largas → truncar
            try:
                cmdline = proc.cmdline()
                info["cmdline"] = " ".join(cmdline)[:200]  # máx 200 chars
            except (psutil.AccessDenied, psutil.ZombieProcess):
                info["cmdline"] = "[sin acceso]"

            info["cpu_percent"]    = round(info.get("cpu_percent") or 0.0, 2)
            info["memory_percent"] = round(info.get("memory_percent") or 0.0, 2)

            # Memoria en MB para legibilidad
            try:
                mem_info = proc.memory_info()
                info["memory_rss_mb"] = round(mem_info.rss / 1e6, 1)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                info["memory_rss_mb"] = 0.0

            processes.append(info)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Ordenar
    key_map = {
        "cpu":    lambda p: p.get("cpu_percent", 0),
        "memory": lambda p: p.get("memory_percent", 0),
        "io":     lambda p: p.get("memory_rss_mb", 0),  # Aproximación con RSS
    }
    sort_key = key_map.get(sort_by, key_map["cpu"])
    processes.sort(key=sort_key, reverse=True)

    return {
        "total_processes": len(psutil.pids()),
        "shown": min(limit, len(processes)),
        "sorted_by": sort_by,
        "processes": processes[:limit],
    }


def kill_process(pid: int, force: bool = False) -> dict:
    """
    Termina un proceso por PID.
    
    - force=False → SIGTERM (el proceso puede limpiar antes de morir)
    - force=True  → SIGKILL (terminación inmediata, sin posibilidad de limpieza)
    
    Retorna información sobre el estado antes/después de la operación.
    """
    # Capturar info del proceso ANTES de matarlo (para el informe)
    try:
        proc = psutil.Process(pid)
        pre_info = {
            "pid":     pid,
            "name":    proc.name(),
            "status":  proc.status(),
            "user":    proc.username(),
            "cpu_pct": round(proc.cpu_percent(interval=0.1), 2),
            "mem_mb":  round(proc.memory_info().rss / 1e6, 1),
        }
    except psutil.NoSuchProcess:
        return {"success": False, "error": f"El proceso con PID {pid} no existe"}
    except psutil.AccessDenied:
        return {
            "success": False,
            "error":   f"Sin permisos para acceder al proceso {pid}",
            "hint":    "Puede que necesites ejecutar el servidor MCP con sudo",
        }

    # Enviar señal
    sig = signal.SIGKILL if force else signal.SIGTERM
    sig_name = "SIGKILL" if force else "SIGTERM"

    try:
        os.kill(pid, sig)

        # Esperar confirmación (máx 3s)
        import time
        for _ in range(30):
            time.sleep(0.1)
            if not psutil.pid_exists(pid):
                break

        still_alive = psutil.pid_exists(pid)
        return {
            "success":      not still_alive,
            "signal_sent":  sig_name,
            "process_before": pre_info,
            "still_alive":  still_alive,
            "message": (
                f"Proceso '{pre_info['name']}' (PID {pid}) terminado correctamente"
                if not still_alive else
                f"Señal {sig_name} enviada, pero el proceso sigue vivo. Considera usar force=True"
            ),
        }

    except ProcessLookupError:
        return {"success": True, "message": "El proceso ya no existe (terminó por sí solo)"}
    except PermissionError:
        return {
            "success": False,
            "error":   "Sin permisos para enviar señal al proceso",
            "hint":    "Ejecuta el servidor MCP con los mismos permisos que el proceso objetivo",
        }


def _is_system_process(info: dict) -> bool:
    """Heurística simple para identificar procesos del sistema en Linux."""
    system_users = {"root", "daemon", "www-data", "nobody", "systemd-network",
                    "systemd-resolve", "messagebus", "syslog", "uuidd", "_apt"}
    system_names = {"kthreadd", "ksoftirqd", "kworker", "migration", "rcu_sched",
                    "rcu_bh", "watchdog", "kdevtmpfs", "netns", "khungtaskd"}

    if info.get("username") in system_users and info.get("pid", 9999) < 100:
        return True
    if info.get("name") in system_names:
        return True
    return False