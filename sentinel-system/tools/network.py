"""
tools/network.py
Conexiones de red activas y consumo de ancho de banda por proceso.
"""

import ipaddress
import psutil
from collections import defaultdict


# Rangos de red privada / local → no se marcan como "externas"
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def get_network_stats(
    show_listening: bool = True,
    show_established: bool = True,
    flag_external: bool = True,
) -> dict:
    """
    Devuelve conexiones de red activas agrupadas por proceso.
    Detecta conexiones a IPs externas (no LAN/localhost).
    """
    # Mapa PID → proceso (para enriquecer las conexiones con nombre)
    pid_to_proc: dict[int, dict] = {}
    for proc in psutil.process_iter(["pid", "name", "username"]):
        try:
            info = proc.as_dict(attrs=["pid", "name", "username"])
            pid_to_proc[info["pid"]] = info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Obtener todas las conexiones de red
    try:
        all_conns = psutil.net_connections(kind="inet")
    except psutil.AccessDenied:
        return {
            "error": "Sin permisos para listar conexiones de red",
            "hint":  "Ejecuta el servidor MCP con sudo para ver todas las conexiones",
        }

    connections = []
    external_connections = []

    for conn in all_conns:
        status = conn.status

        # Filtrar por tipo de conexión solicitado
        if status == "LISTEN" and not show_listening:
            continue
        if status == "ESTABLISHED" and not show_established:
            continue
        if status not in ("LISTEN", "ESTABLISHED", "TIME_WAIT", "CLOSE_WAIT"):
            continue  # Ignorar estados intermedios de poco interés

        # Construir entrada de conexión
        laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "—"
        raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "—"

        is_external = False
        if flag_external and conn.raddr:
            is_external = _is_external_ip(conn.raddr.ip)

        proc_info = pid_to_proc.get(conn.pid, {})

        entry = {
            "pid":          conn.pid,
            "process_name": proc_info.get("name", "desconocido"),
            "user":         proc_info.get("username", "?"),
            "local_addr":   laddr,
            "remote_addr":  raddr,
            "status":       status,
            "family":       "IPv6" if conn.family.name == "AF_INET6" else "IPv4",
            "is_external":  is_external,
        }
        connections.append(entry)
        if is_external:
            external_connections.append(entry)

    # Estadísticas de red (I/O global)
    net_io = psutil.net_io_counters()
    io_stats = {
        "bytes_sent_mb":   round(net_io.bytes_sent / 1e6, 2),
        "bytes_recv_mb":   round(net_io.bytes_recv / 1e6, 2),
        "packets_sent":    net_io.packets_sent,
        "packets_recv":    net_io.packets_recv,
        "errors_in":       net_io.errin,
        "errors_out":      net_io.errout,
        "drops_in":        net_io.dropin,
        "drops_out":       net_io.dropout,
    }

    # Interfaces de red
    interfaces = _get_interfaces()

    # Alerta si hay conexiones externas en procesos no habituales
    suspicious = _flag_suspicious(external_connections)

    return {
        "total_connections": len(connections),
        "external_count":    len(external_connections),
        "suspicious_alerts": suspicious,
        "connections":       connections,
        "global_io":         io_stats,
        "interfaces":        interfaces,
    }


def _is_external_ip(ip_str: str) -> bool:
    """Devuelve True si la IP no es privada/local."""
    try:
        addr = ipaddress.ip_address(ip_str)
        return not any(addr in network for network in _PRIVATE_NETWORKS)
    except ValueError:
        return False


def _get_interfaces() -> list[dict]:
    """Devuelve info básica de las interfaces de red activas."""
    interfaces = []
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for iface_name, addr_list in addrs.items():
        iface_stats = stats.get(iface_name)
        if not iface_stats or not iface_stats.isup:
            continue

        ipv4 = next(
            (a.address for a in addr_list if a.family.name == "AF_INET"),
            None,
        )
        interfaces.append({
            "name":    iface_name,
            "ipv4":    ipv4,
            "speed_mbps": iface_stats.speed,
            "mtu":     iface_stats.mtu,
            "is_up":   iface_stats.isup,
        })

    return interfaces


def _flag_suspicious(external_conns: list[dict]) -> list[dict]:
    """
    Heurística simple para marcar conexiones potencialmente sospechosas.
    Criterios: procesos desconocidos con conexiones externas, puertos raros, etc.
    """
    # Procesos legítimos comunes que conectan al exterior
    known_external = {
        "firefox", "chrome", "chromium", "brave", "curl", "wget", "apt",
        "snap", "snapd", "python3", "python", "node", "java", "ssh",
        "git", "docker", "containerd", "spotify", "slack", "teams",
        "code", "code-oss", "electron",
    }

    suspicious = []
    for conn in external_conns:
        proc = (conn.get("process_name") or "").lower()
        if proc not in known_external:
            suspicious.append({
                "pid":          conn["pid"],
                "process":      conn["process_name"],
                "remote_addr":  conn["remote_addr"],
                "reason":       "Proceso con conexión externa no reconocido",
                "severity":     "info",  # No es una alerta crítica, solo informativa
            })

    return suspicious[:20]  # Limitar a 20 alertas máximo