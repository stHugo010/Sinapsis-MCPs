#!/usr/bin/env python3
"""
Google Calendar MCP Server - Entry Point

Este script inicia el servidor MCP de Google Calendar.
Requiere que auth_setup.py haya sido ejecutado previamente.
"""

from mcp_google_calendar import create_server


def main():
    """
    Punto de entrada principal del servidor.
    
    Crea y ejecuta el servidor MCP de Google Calendar.
    El token de autenticación (token.json) debe existir previamente.
    """
    try:
        server = create_server()
        server.run()
    except FileNotFoundError as e:
        print(f"Error de autenticación: {e}")
        print("\nPara configurar la autenticación:")
        print("  1. Descarga credentials.json desde Google Cloud Console")
        print("  2. Colócalo en el directorio del servidor")
        print("  3. Ejecuta: python auth_setup.py")
        print("  4. Sigue las instrucciones en el navegador")
        exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        exit(1)


if __name__ == "__main__":
    main()