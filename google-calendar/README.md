# Google Calendar MCP

Servidor MCP para gestionar Google Calendar. Permite crear y editar eventos, buscar huecos libres, manejar eventos recurrentes, trabajar con multiples calendarios y personalizar eventos con colores y recordatorios.

## Herramientas

### Gestion de eventos

**`list_events`**
Lista los proximos eventos.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `max_results` | int | 10 | Numero maximo de eventos a devolver |
| `calendar_id` | str | `"primary"` | ID del calendario |

**`create_event`**
Crea un nuevo evento.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `title` | str | Si | Titulo del evento |
| `start` | str | Si | Hora de inicio (ISO 8601) |
| `end` | str | Si | Hora de fin (ISO 8601) |
| `description` | str | No | Descripcion del evento |
| `location` | str | No | Ubicacion del evento |
| `calendar_id` | str | No | ID del calendario (por defecto: primary) |

**`update_event`**
Actualiza un evento existente.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `event_id` | str | Si | ID del evento |
| `title` | str | No | Nuevo titulo |
| `start` | str | No | Nueva hora de inicio (ISO 8601) |
| `end` | str | No | Nueva hora de fin (ISO 8601) |
| `description` | str | No | Nueva descripcion |
| `calendar_id` | str | No | ID del calendario |

**`delete_event`**
Elimina un evento.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `event_id` | str | Si | ID del evento |
| `calendar_id` | str | No | ID del calendario (por defecto: primary) |

### Busqueda

**`find_free_slots`**
Encuentra huecos libres en un dia concreto.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `date` | str | — | Fecha en formato YYYY-MM-DD |
| `duration_minutes` | int | 60 | Duracion necesaria en minutos |
| `start_hour` | int | 8 | Inicio del horario laboral |
| `end_hour` | int | 20 | Fin del horario laboral |
| `calendar_id` | str | `"primary"` | ID del calendario |

**`search_events`**
Busca eventos por texto.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `query` | str | Si | Texto a buscar |
| `max_results` | int | No | Numero maximo de resultados |
| `calendar_id` | str | No | ID del calendario |

**`find_conflicts`**
Detecta eventos solapados en un rango de tiempo.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `start` | str | Si | Inicio del rango (ISO 8601) |
| `end` | str | Si | Fin del rango (ISO 8601) |
| `calendar_id` | str | No | ID del calendario |

**`get_busy_times`**
Devuelve los bloques ocupados para coordinacion de agenda.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `date` | str | Si | Fecha en formato YYYY-MM-DD |
| `calendar_id` | str | No | ID del calendario |

### Multiples calendarios

**`list_calendars`**
Lista todos los calendarios de la cuenta.

**`get_calendar_details`**
Devuelve los detalles de un calendario especifico.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `calendar_id` | str | Si | ID del calendario |

### Eventos recurrentes

**`create_recurring_event`**
Crea un evento recurrente.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `title` | str | Si | Titulo del evento |
| `start` | str | Si | Inicio de la primera ocurrencia (ISO 8601) |
| `end` | str | Si | Fin de la primera ocurrencia (ISO 8601) |
| `frequency` | str | Si | `DAILY`, `WEEKLY`, `MONTHLY` o `YEARLY` |
| `by_day` | list | No | Dias de la semana: `["MO", "TU", "WE", "TH", "FR", "SA", "SU"]` |
| `count` | int | No | Numero de ocurrencias |
| `until` | str | No | Fecha de fin (YYYYMMDD) |
| `interval` | int | No | Repetir cada N periodos |
| `calendar_id` | str | No | ID del calendario |

### Personalizacion

**`set_event_color`**
Establece el color de un evento.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `event_id` | str | Si | ID del evento |
| `color` | str | Si | Nombre del color (ver colores disponibles) |
| `calendar_id` | str | No | ID del calendario |

**`add_reminder`**
Añade un recordatorio a un evento.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `event_id` | str | Si | ID del evento |
| `minutes_before` | int | Si | Minutos antes del evento |
| `method` | str | No | `popup` (por defecto) o `email` |
| `calendar_id` | str | No | ID del calendario |

**`list_colors`**
Devuelve los colores disponibles para eventos.

Colores disponibles: `lavender`, `sage`, `grape`, `flamingo`, `banana`, `tangerine`, `peacock`, `graphite`, `blueberry`, `basil`, `tomato`

## Recursos

| URI | Descripcion |
|-----|-------------|
| `calendar://today` | Eventos de hoy en formato JSON |
| `calendar://week` | Eventos de la semana actual en formato JSON |

## Prompts

**`schedule_from_notion`** — Prompt de flujo de trabajo para programar automaticamente en Google Calendar tareas importadas desde Notion.

## Configuracion

### Paso 1: Google Cloud Platform

1. Accede a [console.cloud.google.com](https://console.cloud.google.com)
2. Crea o selecciona un proyecto
3. Activa la **Google Calendar API**
4. Ve a **Credenciales** → **Crear credenciales** → **ID de cliente OAuth 2.0**
5. Configura la pantalla de consentimiento (Externa, añade tu email como usuario de prueba)
6. Tipo de aplicacion: **Aplicacion de escritorio**
7. Descarga el JSON y guardalo como `credentials.json` dentro del directorio `google-calendar/`

### Paso 2: Generar el token

```bash
cd google-calendar/
python auth_setup.py
```

Esto abrira una ventana del navegador, pedira que autorices el acceso y generara `token.json` automaticamente. El token se refresca solo cuando expira.

### Paso 3: Claude Desktop

Añade al archivo de configuracion de Claude Desktop:

```json
{
  "mcpServers": {
    "google-calendar": {
      "command": "python",
      "args": ["/ruta/absoluta/a/google-calendar/server.py"]
    }
  }
}
```

## Dependencias

- `google-auth-oauthlib`
- `google-api-python-client`
- `fastmcp`

Instalar con:

```bash
cd google-calendar/
uv pip install -e .
```

## Seguridad

`credentials.json` y `token.json` estan excluidos del control de versiones mediante `.gitignore`. Nunca subas estos archivos al repositorio. Si se exponen accidentalmente, revoca las credenciales de inmediato desde [Google Cloud Console](https://console.cloud.google.com) y genera unas nuevas.

El alcance del token esta limitado unicamente a Google Calendar (`https://www.googleapis.com/auth/calendar`).
