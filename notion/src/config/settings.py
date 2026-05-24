"""
config/settings.py
Configuración centralizada del servidor Notion MCP
"""

import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class NotionConfig:
    """Configuración del servidor Notion MCP"""
    
    # Servidor MCP
    server_name: str = "notion-mcp"
    transport: str = "stdio"
    
    # Logging
    log_level: int = logging.WARNING
    log_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    # Notion API
    api_token: Optional[str] = None
    api_version: str = "2022-06-28"
    
    @classmethod
    def from_env(cls, args: Optional[list[str]] = None) -> "NotionConfig":
        """Crea configuración desde variables de entorno y argumentos CLI"""
        if args is None:
            args = sys.argv
        
        config = cls()
        
        # Modo debug
        if "--dev" in args or "--debug" in args:
            config.log_level = logging.DEBUG
        
        # API Token (OBLIGATORIO)
        config.api_token = os.getenv("NOTION_API_TOKEN")
        if not config.api_token:
            raise ValueError(
                "NOTION_API_TOKEN no encontrado. "
                "Configura la variable de entorno con tu token de integración."
            )
        
        return config
    
    def setup_logging(self) -> logging.Logger:
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=self.log_level,
            format=self.log_format,
            stream=sys.stderr,
        )
        logger = logging.getLogger(self.server_name)
        logger.info(f"Logger configurado - Nivel: {logging.getLevelName(self.log_level)}")
        return logger


# Instancia global de configuración
_config: Optional[NotionConfig] = None


def get_config() -> NotionConfig:
    """Obtiene la configuración global (singleton)"""
    global _config
    if _config is None:
        _config = NotionConfig.from_env()
    return _config


def init_config(args: Optional[list[str]] = None) -> NotionConfig:
    """Inicializa la configuración global"""
    global _config
    _config = NotionConfig.from_env(args)
    return _config