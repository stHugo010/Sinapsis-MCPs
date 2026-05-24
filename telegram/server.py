#!/usr/bin/env python3
"""
Telegram MCP Server - Entry Point

Este script inicia el servidor MCP de Telegram.
No requiere argumentos adicionales ya que las credenciales
se cargan desde variables de entorno.
"""

from mcp_telegram import create_server


def main():
    """
    Punto de entrada principal del servidor.
    
    Crea y ejecuta el servidor MCP de Telegram.
    Las credenciales (TELEGRAM_TOKEN y TELEGRAM_CHAT_ID) deben estar
    configuradas en un archivo .env en el directorio padre.
    """
    try:
        server = create_server()
        server.run()
    except ValueError as e:
        print(f"Error de configuración: {e}")
        print("\nAsegúrate de tener un archivo .env con:")
        print("  TELEGRAM_TOKEN=tu_token_aqui")
        print("  TELEGRAM_CHAT_ID=tu_chat_id_aqui")
        exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        exit(1)


if __name__ == "__main__":
    main()