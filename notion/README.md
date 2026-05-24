# Notion MCP

Servidor MCP para interactuar con Notion. Permite buscar paginas y bases de datos, leer el contenido de paginas, crear paginas, añadir bloques de contenido, listar entradas de bases de datos y crear nuevas entradas.

## Herramientas

**`search_pages`**
Busca paginas y bases de datos en un workspace de Notion.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `query` | str | `""` | Texto a buscar. Cadena vacia devuelve todo el contenido accesible. |
| `filter_type` | str | `""` | Filtrar por tipo: `page` o `database`. Vacio devuelve ambos. |
| `limit` | int | 20 | Numero maximo de resultados (1-100) |

**`get_page`**
Devuelve el contenido completo de una pagina, incluyendo metadatos y todos los bloques de contenido.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `page_id` | str | Si | ID de la pagina en Notion (32 caracteres hexadecimales, con o sin guiones) |

**`create_notion_page`**
Crea una nueva pagina hija.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `parent_id` | str | Si | ID de la pagina padre |
| `title` | str | Si | Titulo de la pagina |
| `content` | str | No | Contenido de texto inicial |

Devuelve el ID y la URL de la pagina creada.

**`append_text`**
Añade un bloque de contenido a una pagina existente.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `page_id` | str | — | ID de la pagina de destino |
| `text` | str | — | Texto a añadir |
| `block_type` | str | `paragraph` | Tipo de bloque: `paragraph`, `heading_1`, `heading_2`, `heading_3`, `bulleted_list_item`, `numbered_list_item`, `to_do`, `quote`, `code` |

**`list_database`**
Lista las entradas de una base de datos.

| Parametro | Tipo | Por defecto | Descripcion |
|-----------|------|-------------|-------------|
| `database_id` | str | — | ID de la base de datos |
| `page_size` | int | 10 | Numero de entradas a devolver (1-100) |

**`create_entry`**
Crea una nueva entrada en una base de datos.

| Parametro | Tipo | Requerido | Descripcion |
|-----------|------|-----------|-------------|
| `database_id` | str | Si | ID de la base de datos |
| `properties` | dict | Si | Propiedades de la entrada en formato de la API de Notion |

## Configuracion

### Token de integracion de Notion

1. Accede a [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Haz clic en **New integration**
3. Dale un nombre, selecciona el workspace y establece los permisos que necesitas (leer/escribir contenido)
4. Copia el **Internal Integration Token**
5. Entra en las paginas y bases de datos a las que quieras acceder, haz clic en el menu `...`, ve a **Connections** y añade tu integracion

### Variable de entorno

Crea un archivo `.env` en la raiz del proyecto (el directorio `mcps/`) con:

```
NOTION_API_TOKEN=secret_xxxxxxxxxxxxxxxxxxxx
```

El servidor lee esta variable al arrancar. Si no esta definida, el servidor no podra iniciarse.

### Claude Desktop

Añade al archivo de configuracion de Claude Desktop:

```json
{
  "mcpServers": {
    "notion": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/ruta/absoluta/a/notion",
      "env": {
        "NOTION_API_TOKEN": "secret_xxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

Puedes definir el token en el bloque `env` de la configuracion de Claude Desktop en lugar de usar un archivo `.env`. El bloque `env` es la opcion mas sencilla.

## Dependencias

- `mcp`
- `requests`

Instalar con:

```bash
cd notion/
uv pip install -e .
```

## Notas

- Los IDs de paginas y bases de datos se encuentran en la URL de cualquier pagina de Notion: `https://notion.so/Titulo-<id-de-32-caracteres>`
- Los IDs se pueden proporcionar con o sin guiones; ambos formatos son validos.
- Las peticiones a la API de Notion tienen un tiempo de espera de 10 segundos.
- La version de la API de Notion utilizada es `2022-06-28`.
