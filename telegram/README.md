# Telegram MCP

Servidor MCP para enviar notificaciones a un chat de Telegram. Actua como hub de notificaciones para otros servidores MCP: recibe eventos de Obsidian, Google Calendar, Notion y el monitor del sistema, y los entrega como mensajes formateados en Telegram.

Los mensajes tienen un limite de velocidad de un minimo de 100ms entre llamadas a la API. Todas las notificaciones enviadas durante una sesion se almacenan en memoria y son accesibles como recurso.

## Herramientas

**`notify_obsidian`**
Envia una notificacion sobre una accion realizada en el vault de Obsidian.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `message` | str | Si | Mensaje de la notificacion |
| `action` | str | No | Tipo de accion (ej: `created`, `updated`, `deleted`, `moved`) |

**`notify_calendar`**
Envia una notificacion sobre un evento de Google Calendar.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `message` | str | Si | Mensaje de la notificacion |
| `event_title` | str | No | Titulo del evento |

**`notify_notion`**
Envia una notificacion sobre una tarea o pagina de Notion.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `message` | str | Si | Mensaje de la notificacion |
| `task_title` | str | No | Titulo de la tarea o pagina |

**`notify_system`**
Envia una alerta del sistema.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `message` | str | — | Mensaje de la alerta |
| `level` | str | `info` | Nivel de severidad: `info`, `warning` o `critical` |

**`send_summary`**
Envia un informe de resumen con multiples elementos como un unico mensaje formateado.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `title` | str | Si | Titulo del resumen |
| `items` | list | Si | Lista de elementos de texto (se renderizan como lista con puntos) |
| `source` | str | No | Etiqueta de origen para filtrar en el recurso de log |

## Recursos

| URI | Descripcion |
|-----|-------------|
| `telegram://log` | Historial completo de notificaciones de la sesion actual |
| `telegram://log/{source}` | Historial filtrado por origen: `obsidian`, `calendar`, `notion` o `system` |

## Prompts

**`daily_report`** — Instrucciones para generar un resumen diario estructurado de todas las herramientas conectadas y enviarlo como mensaje de Telegram.

## Configuracion

### Crear un bot de Telegram

1. Abre Telegram y busca `@BotFather`
2. Envia `/newbot` y sigue las instrucciones
3. Copia el **token del bot** que te proporciona al final (formato: `123456789:ABCdef...`)
4. Inicia una conversacion con tu bot o añadelo a un grupo
5. Para obtener tu chat ID, envia un mensaje al bot y abre `https://api.telegram.org/bot<TOKEN>/getUpdates` en el navegador. El campo `chat.id` de la respuesta es tu chat ID.

### Variables de entorno

Crea un archivo `.env` en la raiz del proyecto (el directorio `mcps/`) con:

```
TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHAT_ID=123456789
```

Ambas variables son obligatorias. El servidor no podra iniciarse si alguna falta.

### Claude Desktop

Añade al archivo de configuracion de Claude Desktop:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "python",
      "args": ["/ruta/absoluta/a/telegram/server.py"],
      "env": {
        "TELEGRAM_TOKEN": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ",
        "TELEGRAM_CHAT_ID": "123456789"
      }
    }
  }
}
```

Puedes definir las credenciales en el bloque `env` de la configuracion de Claude Desktop en lugar de usar un archivo `.env`.

## Dependencias

- `fastmcp`
- `httpx`
- `python-dotenv`

Instalar con:

```bash
cd telegram/
uv pip install fastmcp httpx python-dotenv
```
