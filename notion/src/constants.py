"""
constants.py
Constantes del servidor Notion MCP
"""

from typing import Final

# ─── Límites de la API ────────────────────────────────────────────────────────
PAGE_SIZE_MIN: Final[int] = 1
PAGE_SIZE_MAX: Final[int] = 100
PAGE_SIZE_DEFAULT: Final[int] = 10

SEARCH_LIMIT_MIN: Final[int] = 1
SEARCH_LIMIT_MAX: Final[int] = 100
SEARCH_LIMIT_DEFAULT: Final[int] = 20

# ─── Tipos de objetos Notion ──────────────────────────────────────────────────
OBJECT_TYPE_PAGE: Final[str] = "page"
OBJECT_TYPE_DATABASE: Final[str] = "database"

# ─── Tipos de propiedades ─────────────────────────────────────────────────────
PROPERTY_TYPES: Final[list[str]] = [
    "title",
    "rich_text",
    "number",
    "select",
    "multi_select",
    "date",
    "people",
    "files",
    "checkbox",
    "url",
    "email",
    "phone_number",
    "formula",
    "relation",
    "rollup",
    "created_time",
    "created_by",
    "last_edited_time",
    "last_edited_by",
]

# ─── Tipos de bloques ─────────────────────────────────────────────────────────
BLOCK_TYPES: Final[list[str]] = [
    "paragraph",
    "heading_1",
    "heading_2",
    "heading_3",
    "bulleted_list_item",
    "numbered_list_item",
    "to_do",
    "toggle",
    "code",
    "quote",
    "callout",
    "divider",
]

# ─── Instrucciones del servidor MCP ───────────────────────────────────────────
MCP_INSTRUCTIONS: Final[str] = """
Eres un asistente de Notion. Tienes acceso a herramientas para:
- Buscar páginas y bases de datos
- Leer contenido de páginas
- Crear nuevas páginas
- Añadir contenido a páginas existentes
- Listar y crear entradas en bases de datos

IMPORTANTE:
- Las IDs de Notion tienen formato: 32 caracteres hexadecimales con guiones
- Siempre valida las IDs antes de usarlas
- Usa la herramienta de búsqueda para encontrar páginas/databases
- El contenido de las páginas se gestiona mediante bloques
"""