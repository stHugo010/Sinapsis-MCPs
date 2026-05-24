"""
config package
Configuración centralizada del sistema
"""

from .settings import SentinelConfig, get_config, init_config

__all__ = ["SentinelConfig", "get_config", "init_config"]