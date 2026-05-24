"""
config package
Configuración del servidor Notion MCP
"""

from .settings import NotionConfig, get_config, init_config

__all__ = ["NotionConfig", "get_config", "init_config"]