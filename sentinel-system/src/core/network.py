"""
core/network.py
Monitorización de conexiones de red y estadísticas
"""

import psutil
from typing import Dict, Any, List

from ..utils import now_iso, is_external_ip


def get_network_stats(
    show_listening: bool = True,
    show_established: bool = True,
    flag_external: bool = True,
) -> Dict[str, Any]:
    """
    Obtiene conexiones de red activas y estadísticas.
    
    Args:
        show_listening: Incluir puertos en escucha
        show_established: Incluir conexiones establecidas
        flag_external: Marcar conexiones externas
    
    Returns:
        Dict con conexiones y estadísticas de red
    """
    connections = []
    
    for conn in psutil.net_connections(kind='inet'):
        # Filtrar según estado
        if conn.status == 'LISTEN' and not show_listening:
            continue
        if conn.status == 'ESTABLISHED' and not show_established:
            continue
        
        # Obtener información del proceso
        proc_name = "unknown"
        if conn.pid:
            try:
                proc = psutil.Process(conn.pid)
                proc_name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Parsear direcciones
        local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "unknown"
        remote_addr = "unknown"
        is_external = False
        
        if conn.raddr:
            remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}"
            if flag_external:
                is_external = is_external_ip(conn.raddr.ip)
        
        connections.append({
            "pid": conn.pid,
            "process": proc_name,
            "local": local_addr,
            "remote": remote_addr,
            "status": conn.status,
            "family": "IPv4" if conn.family == 2 else "IPv6",
            "external": is_external if flag_external else None,
        })
    
    # Estadísticas de tráfico
    net_io = psutil.net_io_counters()
    
    return {
        "timestamp": now_iso(),
        "connections": connections,
        "total_connections": len(connections),
        "io_stats": {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errors_in": net_io.errin,
            "errors_out": net_io.errout,
            "drops_in": net_io.dropin,
            "drops_out": net_io.dropout,
        },
    }