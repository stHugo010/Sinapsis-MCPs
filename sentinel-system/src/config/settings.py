"""
config/settings.py
Configuración centralizada del servidor Sentinel
"""

import logging
import sys
from dataclasses import dataclass
from typing import Optional

from ..constants import (
    CPU_ALERT_THRESHOLD,
    RAM_ALERT_THRESHOLD,
    DISK_ALERT_THRESHOLD,
    PERFORMANCE_INTERVAL_DEFAULT,
)


@dataclass
class SentinelConfig:
    """Configuración del servidor System Sentinel"""
    
    # Servidor MCP
    server_name: str = "system-sentinel"
    transport: str = "stdio"
    
    # Logging
    log_level: int = logging.WARNING
    log_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    # Performance Sampler
    sampler_enabled: bool = False
    sampler_interval: int = PERFORMANCE_INTERVAL_DEFAULT
    
    # Alertas
    cpu_alert_threshold: float = CPU_ALERT_THRESHOLD
    ram_alert_threshold: float = RAM_ALERT_THRESHOLD
    disk_alert_threshold: float = DISK_ALERT_THRESHOLD
    
    # Seguridad
    enable_guardian: bool = True
    require_kill_confirmation: bool = True
    
    @classmethod
    def from_args(cls, args: Optional[list[str]] = None) -> "SentinelConfig":
        """Crea configuración desde argumentos de línea de comandos"""
        if args is None:
            args = sys.argv
        
        config = cls()
        
        # Modo debug
        if "--dev" in args or "--debug" in args:
            config.log_level = logging.DEBUG
        
        # Auto-iniciar sampler
        if "--sampler" in args:
            config.sampler_enabled = True
        
        # Deshabilitar guardian (PELIGROSO, solo para testing)
        if "--no-guardian" in args:
            config.enable_guardian = False
        
        return config
    
    def setup_logging(self) -> logging.Logger:
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=self.log_level,
            format=self.log_format,
            stream=sys.stderr,  # MCP usa stdout para el protocolo
        )
        logger = logging.getLogger(self.server_name)
        logger.info(f"Logger configurado - Nivel: {logging.getLevelName(self.log_level)}")
        return logger


# Instancia global de configuración
_config: Optional[SentinelConfig] = None


def get_config() -> SentinelConfig:
    """Obtiene la configuración global (singleton)"""
    global _config
    if _config is None:
        _config = SentinelConfig.from_args()
    return _config


def init_config(args: Optional[list[str]] = None) -> SentinelConfig:
    """Inicializa la configuración global"""
    global _config
    _config = SentinelConfig.from_args(args)
    return _config