# Sentinel System MCP

Servidor MCP para monitorizacion y diagnostico en Linux. Proporciona informacion en tiempo real sobre CPU, RAM, disco, temperatura, procesos en ejecucion, hardware (GPU, bateria, ventiladores), conexiones de red y logs del sistema. Incluye un muestreador de rendimiento en segundo plano y un guardian de seguridad que evita la terminacion accidental de procesos criticos.

## Herramientas

**`system_health`**
Devuelve un snapshot completo del sistema: uso de CPU, RAM, disco, swap y temperaturas.

No requiere parametros.

**`top_processes`**
Lista los procesos en ejecucion ordenados por consumo de recursos.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `sort_by` | str | `cpu` | Criterio de ordenacion: `cpu`, `memory` o `io` |
| `limit` | int | 10 | Numero de procesos a devolver (1-50) |
| `include_system` | bool | false | Incluir procesos del kernel y del sistema |

**`terminate_process`**
Termina un proceso por su PID. Protegido por el guardian de seguridad (ver seccion Seguridad).

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `pid` | int | Si | ID del proceso |
| `force` | bool | No | `true` envia SIGKILL, `false` (por defecto) envia SIGTERM |
| `reason` | str | No | Motivo de la terminacion (se registra en el log de auditoria) |

**`read_system_logs`**
Lee logs del sistema desde journalctl o syslog.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `lines` | int | 50 | Numero de lineas de log a devolver (10-500) |
| `level` | str | `all` | Filtrar por nivel: `error`, `warning`, `info` o `all` |
| `since_minutes` | int | 60 | Ventana de tiempo en minutos (1-1440) |

**`network_connections`**
Lista las conexiones de red activas.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `show_listening` | bool | true | Incluir puertos en escucha |
| `show_established` | bool | true | Incluir conexiones establecidas |
| `flag_external` | bool | true | Marcar conexiones a IPs externas |

**`hardware_info`**
Devuelve informacion del hardware: bateria, GPU y ventiladores.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `include_battery` | bool | true | Incluir estado y nivel de carga de la bateria |
| `include_fans` | bool | true | Incluir lecturas de RPM de los ventiladores |
| `include_gpu` | bool | true | Incluir informacion de GPU (compatible con NVIDIA, AMD e Intel) |

**`performance_history`**
Devuelve el historial de uso de CPU y RAM con deteccion de picos.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `last_n` | int | 60 | Numero de muestras a devolver (1-1440) |
| `metric` | str | `both` | Metrica a devolver: `cpu`, `ram` o `both` |
| `alert_cpu_threshold` | float | 80 | Porcentaje de CPU para marcar picos |
| `alert_ram_threshold` | float | 85 | Porcentaje de RAM para marcar picos |

**`manage_performance_sampler`**
Controla el muestreador de rendimiento en segundo plano.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `action` | str | Si | `start`, `stop`, `clear` o `status` |
| `interval_seconds` | int | No | Intervalo de muestreo en segundos (10-3600). Solo se usa con `start`. |

## Configuracion

El servidor utiliza un dataclass `SentinelConfig` con los siguientes valores por defecto:

| Ajuste | Por defecto | Descripcion |
|--------|-------------|-------------|
| Umbral de alerta de CPU | 80% | Genera una advertencia en `performance_history` |
| Umbral de alerta de RAM | 85% | Genera una advertencia en `performance_history` |
| Umbral de alerta de disco | 90% | Se informa en `system_health` |
| Guardian | activado | Bloquea la terminacion de procesos criticos |
| Muestreador | desactivado | Debe iniciarse explicitamente con `manage_performance_sampler` |

### Modos de ejecucion

```bash
# Modo estandar (stdio, para Claude Desktop)
python -m src.server

# Modo depuracion (log detallado)
python -m src.server --dev

# Con el muestreador en segundo plano activado al arrancar
python -m src.server --sampler

# Desactivar el guardian de procesos (no recomendado)
python -m src.server --no-guardian
```

### Claude Desktop

Añade al archivo de configuracion de Claude Desktop:

```json
{
  "mcpServers": {
    "sentinel-system": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/ruta/absoluta/a/sentinel-system"
    }
  }
}
```

## Seguridad

### Guardian de procesos

La herramienta `terminate_process` esta protegida por un guardian que bloquea la terminacion de:

- Procesos del kernel e init: `systemd`, `init`, `kthreadd`
- Servicios criticos: `sshd`, `NetworkManager`, `dbus-daemon`
- Cualquier proceso con PID inferior a 100
- Procesos propiedad de usuarios del sistema (`root`, `systemd-*`)

Cada terminacion exitosa queda registrada con el PID, nombre del proceso, flag de forzado y motivo proporcionado.

### Formato del log de auditoria

```
[WARNING] AUDITORIA: Proceso terminado | PID=1234 | Nombre=firefox | Force=False | Razon='Alto consumo de RAM'
```

## Dependencias

- `mcp`
- `psutil`

Instalar con:

```bash
cd sentinel-system/
uv pip install mcp psutil
```

O usando el archivo del proyecto:

```bash
cd sentinel-system/src/
uv pip install -e .
```
