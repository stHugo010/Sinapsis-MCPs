"""
core/processes.py
Lógica de negocio para gestión de procesos
"""

import signal
import psutil
from typing import Dict, Any, List, Optional

from ..utils import now_iso
from ..constants import SortCriteria


def list_processes(
    sort_by: str = "cpu",
    limit: int = 10,
    include_system: bool = False,
) -> Dict[str, Any]:
    """
    Lista procesos del sistema ordenados por consumo de recursos.
    
    Args:
        sort_by: Criterio de ordenación ("cpu", "memory", "io")
        limit: Número máximo de procesos
        include_system: Incluir procesos del sistema
    
    Returns:
        Dict con lista de procesos y metadata
    """
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 
                                      'memory_percent', 'status', 'create_time']):
        try:
            pinfo = proc.info
            
            # Filtrar procesos del sistema si es necesario
            if not include_system:
                username = pinfo.get('username', '')
                if username in ['root', 'daemon', 'bin', 'sys', 'systemd-network']:
                    continue
            
            processes.append({
                "pid": pinfo['pid'],
                "name": pinfo['name'],
                "username": pinfo.get('username', 'unknown'),
                "cpu_percent": round(pinfo.get('cpu_percent', 0.0), 1),
                "memory_percent": round(pinfo.get('memory_percent', 0.0), 1),
                "status": pinfo.get('status', 'unknown'),
                "create_time": pinfo.get('create_time', 0),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Ordenar según criterio
    if sort_by == SortCriteria.CPU:
        processes.sort(key=lambda p: p['cpu_percent'], reverse=True)
    elif sort_by == SortCriteria.MEMORY:
        processes.sort(key=lambda p: p['memory_percent'], reverse=True)
    elif sort_by == SortCriteria.IO:
        # IO es más complejo, por ahora ordenar por CPU como fallback
        processes.sort(key=lambda p: p['cpu_percent'], reverse=True)
    
    # Limitar resultados
    processes = processes[:limit]
    
    return {
        "timestamp": now_iso(),
        "sort_by": sort_by,
        "limit": limit,
        "include_system": include_system,
        "total_processes": len(processes),
        "processes": processes,
    }


def kill_process(pid: int, force: bool = False) -> Dict[str, Any]:
    """
    Termina un proceso del sistema.
    
    Args:
        pid: ID del proceso
        force: Si True usa SIGKILL, si False usa SIGTERM
    
    Returns:
        Dict con resultado de la operación
    """
    try:
        proc = psutil.Process(pid)
        
        # Obtener info antes de terminar
        process_info = {
            "pid": pid,
            "name": proc.name(),
            "username": proc.username(),
            "cpu_percent": proc.cpu_percent(),
            "memory_percent": proc.memory_percent(),
            "status_before": proc.status(),
        }
        
        # Terminar proceso
        if force:
            proc.kill()  # SIGKILL
            signal_used = "SIGKILL"
        else:
            proc.terminate()  # SIGTERM
            signal_used = "SIGTERM"
        
        # Esperar un poco y verificar
        try:
            proc.wait(timeout=3)
            terminated = True
        except psutil.TimeoutExpired:
            terminated = False
        
        return {
            "success": True,
            "terminated": terminated,
            "signal": signal_used,
            "process": process_info,
            "message": f"Proceso {pid} ({process_info['name']}) terminado con {signal_used}",
        }
        
    except psutil.NoSuchProcess:
        return {
            "success": False,
            "error": f"Proceso con PID {pid} no existe",
        }
    except psutil.AccessDenied:
        return {
            "success": False,
            "error": f"Permiso denegado para terminar proceso {pid}",
            "hint": "Puede requerir permisos de root/sudo",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error al terminar proceso: {str(e)}",
        }


def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
    """Obtiene información detallada de un proceso"""
    try:
        proc = psutil.Process(pid)
        return {
            "pid": pid,
            "name": proc.name(),
            "username": proc.username(),
            "status": proc.status(),
            "cpu_percent": round(proc.cpu_percent(), 1),
            "memory_percent": round(proc.memory_percent(), 1),
            "memory_mb": round(proc.memory_info().rss / 1024 / 1024, 1),
            "num_threads": proc.num_threads(),
            "create_time": proc.create_time(),
            "cmdline": " ".join(proc.cmdline()[:5]),  # Primeros 5 argumentos
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None