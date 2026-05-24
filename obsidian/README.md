# Obsidian MCP

Servidor MCP para gestionar un vault de Obsidian. Permite leer, crear, mover y eliminar notas, aplicar plantillas, editar el frontmatter, buscar por palabra clave o backlinks y gestionar carpetas.

## Herramientas

### Notas

**`find_note`**
Busca una nota por nombre y devuelve su contenido completo.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `nombre` | str | Si | Nombre de la nota sin la extension `.md` |

**`list_templates`**
Lista todas las plantillas disponibles en la carpeta de plantillas.

Devuelve una lista de nombres de plantilla (sin extension `.md`).

**`create_note_from_template`**
Crea una nueva nota a partir de una plantilla, sustituyendo `{{date}}` por la fecha de hoy.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `note_name` | str | Si | Nombre para la nueva nota |
| `folder` | str | Si | Carpeta de destino (ruta relativa dentro del vault) |
| `template_name` | str | Si | Nombre de la plantilla (sin extension `.md`) |

**`delete_note`**
Elimina una nota del vault.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `note_name` | str | Si | Nombre de la nota sin la extension `.md` |

**`move_note`**
Mueve una nota a otra carpeta dentro del vault.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `note_name` | str | Si | Nombre de la nota sin la extension `.md` |
| `destination_folder` | str | Si | Ruta de destino relativa a la raiz del vault (ej: `Archivo` o `Proyectos/TFG`) |

**`update_frontmatter`**
Actualiza campos del frontmatter de una nota sin modificar el cuerpo.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `note_name` | str | Si | Nombre de la nota sin la extension `.md` |
| `updates` | dict | Si | Pares clave-valor a establecer o actualizar en el frontmatter |

### Busqueda

**`buscar_palabra`**
Devuelve todas las notas que contienen una palabra clave.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `keyword` | str | Si | Palabra o frase a buscar |

**`buscar_backlinks`**
Encuentra todas las notas que enlazan a la nota indicada mediante la sintaxis de wiki-link de Obsidian (`[[nombre_nota]]`).

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `nombre_nota` | str | Si | Nombre de la nota de la que buscar backlinks |

### Carpetas

**`explore_folder`**
Lista el contenido de una carpeta del vault. Mas eficiente que cargar la estructura completa del vault en vaults grandes.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `path` | str | `""` | Ruta de la carpeta relativa a la raiz del vault. Cadena vacia para la raiz. |

**`create_folder`**
Crea una nueva carpeta dentro del vault.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `folder_name` | str | Si | Ruta de la carpeta relativa a la raiz del vault |

## Recursos

| URI | Descripcion |
|-----|-------------|
| `obsidian://vault/structure` | Arbol de directorios completo del vault |
| `obsidian://vault/tags` | Indice de etiquetas con recuento de notas |
| `obsidian://note/{nombre}` | Contenido de una nota especifica |
| `obsidian://templates` | Lista de plantillas disponibles |

## Prompts

**`crear_nota`** — Flujo guiado para crear una nueva nota usando la plantilla adecuada.

**`archivar_nota`** — Flujo para mover una nota a la carpeta de archivo.

**`nota_diaria`** — Flujo para crear o actualizar la nota diaria de hoy.

## Configuracion

### Ruta del vault

Por defecto el servidor busca el vault en `~/Documents/Obsidian` y las plantillas en `{vault}/Templates`. Puedes sobreescribir ambas rutas pasando argumentos:

```bash
python mcp_obsidian.py /ruta/al/vault /ruta/a/las/plantillas
```

### Claude Desktop

Añade al archivo de configuracion de Claude Desktop:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": ["/ruta/absoluta/a/obsidian/mcp_obsidian.py"]
    }
  }
}
```

Si tu vault no esta en `~/Documents/Obsidian`, pasalo como argumento:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": [
        "/ruta/absoluta/a/obsidian/mcp_obsidian.py",
        "/ruta/absoluta/a/tu/vault",
        "/ruta/absoluta/a/tus/plantillas"
      ]
    }
  }
}
```

## Dependencias

- `fastmcp`

Instalar con:

```bash
cd obsidian/
uv pip install fastmcp
```

## Notas

- Los nombres de nota siempre se especifican sin la extension `.md`.
- El servidor omite los directorios ocultos (los que empiezan por `.`) al recorrer el vault.
- Se recomienda usar `explore_folder` en lugar de cargar la estructura completa del vault cuando el vault es grande.
