#!/usr/bin/env python3
"""
Google Calendar OAuth2 Setup

Script para generar token.json desde credentials.json.
Solo necesita ejecutarse una vez para autorizar el acceso.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")


def main():
    """
    Genera token.json a través del flujo OAuth2.
    
    Abre el navegador para que el usuario autorice el acceso
    a Google Calendar y guarda el token localmente.
    """
    print("=== Google Calendar OAuth2 Setup ===\n")
    
    # Verificar que existe credentials.json
    if not os.path.exists(CREDS_PATH):
        print(f"❌ Error: No se encontró {CREDS_PATH}\n")
        print("Para obtener credentials.json:")
        print("  1. Ve a https://console.cloud.google.com")
        print("  2. Crea o selecciona un proyecto")
        print("  3. Habilita Google Calendar API")
        print("  4. Crea credenciales OAuth 2.0")
        print("  5. Descarga el JSON como 'credentials.json'")
        print("  6. Colócalo en este directorio")
        return
    
    creds = None
    
    # Verificar si ya existe token
    if os.path.exists(TOKEN_PATH):
        print(f"ℹ️  Token existente encontrado en {TOKEN_PATH}")
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # Si no hay token válido, generar uno nuevo
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refrescando token expirado...")
            creds.refresh(Request())
        else:
            print("🌐 Iniciando flujo de autenticación OAuth2...")
            print("Se abrirá tu navegador. Autoriza el acceso a Google Calendar.\n")
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Guardar token
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        
        print(f"\n✅ Token guardado correctamente en {TOKEN_PATH}")
    else:
        print("✅ Token válido ya existe")
    
    print("\n=== Configuración completada ===")
    print("Ya puedes ejecutar: python server.py")


if __name__ == "__main__":
    main()