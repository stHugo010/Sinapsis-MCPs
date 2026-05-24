"""
security/guardian.py

ProcessGuardian: lista negra de procesos críticos que el LLM NUNCA debe poder matar.
Este componente es el diferenciador de seguridad del TFG.

Diseño: fail-safe por defecto. Si hay dudas, bloquea.
"""

import psutil
from dataclasses import dataclass, field


@dataclass
class ProcessGuardian:
    """
    Guardian de seguridad que verifica si es seguro terminar un proceso.
    
    Protege contra:
    1. PIDs bajos del kernel (< 10)
    2. Procesos en la lista negra por nombre
    3. El propio proceso del servidor MCP
    4. Procesos init/systemd (PID 1)
    """

    # Nombres de procesos que NUNCA deben terminarse
    protected_names: set[str] = field(default_factory=lambda: {
        # Kernel y gestión de procesos
        "init", "systemd", "kthreadd", "ksoftirqd", "migration",
        "rcu_sched", "rcu_bh", "watchdog", "kdevtmpfs",
        # Servicios críticos de red y sistema
        "sshd", "NetworkManager", "networkd", "wpa_supplicant",
        "systemd-resolved", "systemd-networkd", "systemd-journald",
        "systemd-udevd", "dbus-daemon", "avahi-daemon",
        # Autenticación y seguridad
        "polkitd", "pam", "login", "gdm", "lightdm", "sddm",
        # Gestión de hardware
        "udevd", "acpid", "irqbalance", "thermald",
        # El propio servidor MCP (nos protegemos a nosotros mismos)
        "python", "python3",  # ← se refinará con PID propio abajo
    })

    # PIDs siempre protegidos
    protected_pids: set[int] = field(default_factory=lambda: {
        0,   # Swapper/idle
        1,   # init / systemd
        2,   # kthreadd
    })

    def __post_init__(self):
        """Añade el PID del propio proceso MCP a la lista protegida."""
        import os
        self.protected_pids.add(os.getpid())
        self.protected_pids.add(os.getppid())  # Proceso padre (shell/Claude Desktop)

    def is_safe_to_kill(self, pid: int) -> dict:
        """
        Verifica si es seguro terminar el proceso con el PID dado.
        
        Returns:
            {"safe": bool, "reason": str}
        """
        # ── Regla 1: PID protegido explícitamente ────────────────────────────
        if pid in self.protected_pids:
            return {
                "safe": False,
                "reason": f"PID {pid} está en la lista de procesos protegidos del sistema",
            }

        # ── Regla 2: PIDs muy bajos son típicamente threads del kernel ────────
        if pid < 10:
            return {
                "safe": False,
                "reason": f"PID {pid} es un proceso del kernel (PIDs < 10 son siempre protegidos)",
            }

        # ── Regla 3: Obtener info real del proceso ────────────────────────────
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            proc_user = proc.username()
            
            # Regla 4: Nombre en lista negra
            # Comprobamos tanto el nombre exacto como si empieza por él
            for protected in self.protected_names:
                if proc_name == protected or proc_name.startswith(f"{protected}:"):
                    return {
                        "safe": False,
                        "reason": f"'{proc_name}' es un proceso del sistema protegido",
                    }

            # ── Regla 5: Procesos de root con PIDs bajos son sospechosos ─────
            if proc_user == "root" and pid < 500:
                return {
                    "safe": False,
                    "reason": (
                        f"Proceso de root con PID bajo ({pid}): "
                        "potencialmente crítico para el sistema"
                    ),
                }

            # ── Regla 6: ¿Es el proceso padre de systemd? ────────────────────
            try:
                parent = proc.parent()
                if parent and parent.pid == 1 and proc_user == "root":
                    return {
                        "safe": False,
                        "reason": (
                            f"'{proc_name}' es hijo directo de init/systemd "
                            "ejecutándose como root (proceso de sistema)"
                        ),
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            # ── Si pasa todas las comprobaciones, es seguro ───────────────────
            return {
                "safe": True,
                "reason": "El proceso no está en la lista de protección",
                "process_info": {
                    "name": proc_name,
                    "user": proc_user,
                    "pid":  pid,
                },
            }

        except psutil.NoSuchProcess:
            return {
                "safe": False,
                "reason": f"El proceso con PID {pid} no existe",
            }
        except psutil.AccessDenied:
            # Si no podemos leer el proceso, es probablemente del sistema
            return {
                "safe": False,
                "reason": (
                    f"Sin acceso al proceso PID {pid}. "
                    "Por seguridad, se bloquea cuando no se puede verificar"
                ),
            }

    def add_protection(self, name: str) -> None:
        """Permite añadir procesos adicionales a la lista de protección en runtime."""
        self.protected_names.add(name)

    def add_protected_pid(self, pid: int) -> None:
        """Permite proteger un PID específico en runtime."""
        self.protected_pids.add(pid)