"""
core/guardian.py
Guardian de seguridad para procesos críticos del sistema
"""

import psutil
from typing import Dict, Any

from ..constants import CRITICAL_PROCESSES, CRITICAL_PROCESS_OWNERS


class ProcessGuardian:
    """
    Guardian de seguridad que previene la terminación de procesos críticos.
    """
    
    def __init__(self):
        self.critical_processes = set(CRITICAL_PROCESSES)
        self.critical_owners = set(CRITICAL_PROCESS_OWNERS)
    
    def is_safe_to_kill(self, pid: int) -> Dict[str, Any]:
        """
        Verifica si es seguro terminar un proceso.
        
        Args:
            pid: ID del proceso
        
        Returns:
            Dict con 'safe' (bool) y 'reason' (str)
        """
        try:
            proc = psutil.Process(pid)
            
            # Verificar nombre del proceso
            proc_name = proc.name().lower()
            if any(critical in proc_name for critical in self.critical_processes):
                return {
                    "safe": False,
                    "reason": f"Proceso crítico del sistema: {proc.name()}",
                    "process_name": proc.name(),
                }
            
            # Verificar propietario
            try:
                username = proc.username()
                if username in self.critical_owners:
                    return {
                        "safe": False,
                        "reason": f"Proceso del sistema operado por usuario crítico: {username}",
                        "process_name": proc.name(),
                        "username": username,
                    }
            except psutil.AccessDenied:
                # Si no podemos ver el usuario, probablemente es del sistema
                return {
                    "safe": False,
                    "reason": "Acceso denegado - probablemente proceso del sistema",
                    "process_name": proc.name(),
                }
            
            # Verificar PID muy bajo (procesos del kernel)
            if pid < 100:
                return {
                    "safe": False,
                    "reason": f"PID muy bajo ({pid}) - probablemente proceso del kernel",
                    "process_name": proc.name(),
                }
            
            # Todo OK
            return {
                "safe": True,
                "reason": "Proceso puede ser terminado de forma segura",
                "process_name": proc.name(),
            }
            
        except psutil.NoSuchProcess:
            return {
                "safe": False,
                "reason": f"Proceso {pid} no existe",
            }
        except Exception as e:
            return {
                "safe": False,
                "reason": f"Error al verificar proceso: {str(e)}",
            }
    
    def add_critical_process(self, process_name: str):
        """Añade un proceso a la lista de críticos"""
        self.critical_processes.add(process_name.lower())
    
    def remove_critical_process(self, process_name: str):
        """Elimina un proceso de la lista de críticos"""
        self.critical_processes.discard(process_name.lower())
    
    def get_critical_processes(self) -> set:
        """Retorna lista de procesos críticos configurados"""
        return self.critical_processes.copy()