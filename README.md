# Coleccion de MCPs

Coleccion de servidores MCP (Model Context Protocol) diseñados para extender Claude con integraciones para herramientas de productividad y gestion del sistema.

Cada servidor es independiente y puede instalarse y configurarse por separado en Claude Desktop.

## Servidores

| Servidor | Descripcion | Herramientas |
|----------|-------------|--------------|
| [google-calendar](./google-calendar/) | Gestiona eventos de Google Calendar, busca huecos libres, maneja eventos recurrentes y multiples calendarios | 14 |
| [obsidian](./obsidian/) | Lee, crea, mueve y busca notas en un vault de Obsidian | 10 |
| [notion](./notion/) | Busca paginas, gestiona bases de datos y crea contenido en Notion | 6 |
| [telegram](./telegram/) | Envia notificaciones y resumenes a un chat de Telegram | 5 |
| [sentinel-system](./sentinel-system/) | Monitoriza el estado del sistema, procesos, hardware, red y logs en Linux | 8 |

## Requisitos

- Python 3.11 o superior (se recomienda 3.14)
- [uv](https://docs.astral.sh/uv/) para la gestion de dependencias
- Claude Desktop

## Instalacion general

Cada servidor tiene sus propias dependencias y configuracion. Consulta el README dentro de cada directorio para instrucciones especificas.

El patron general para cualquier servidor es:

```bash
cd <directorio-del-servidor>
uv venv
source .venv/bin/activate
uv pip install -e .
```

Despues añade el servidor al archivo de configuracion de Claude Desktop:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

## Seguridad

Los archivos sensibles estan excluidos del control de versiones mediante `.gitignore`. Debes crear los siguientes archivos localmente despues de clonar el repositorio:

- `google-calendar/credentials.json` — Descargado desde Google Cloud Console
- `google-calendar/token.json` — Generado ejecutando `auth_setup.py`
- `.env` — Contiene las claves de API para Notion y Telegram (ver el README de cada servidor)

Nunca subas al repositorio `credentials.json`, `token.json` ni archivos `.env`.

## Estructura del proyecto

```
mcps/
├── google-calendar/    # MCP de Google Calendar
├── obsidian/           # MCP del vault de Obsidian
├── notion/             # MCP de Notion
├── telegram/           # MCP de notificaciones de Telegram
├── sentinel-system/    # MCP de monitorizacion del sistema
├── pyproject.toml      # Configuracion del proyecto raiz
└── .gitignore
```
