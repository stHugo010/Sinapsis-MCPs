from datetime import datetime
from fastmcp import FastMCP, Context
from fastmcp.prompts import Message

mcp = FastMCP("obsidian-prompts")

@mcp.prompt(
    name="crear_nota",
    description="Orquesta la creación de una nota consultando las reglas del vault y su estructura actual.",
    tags={"create", "workflow"}
)
async def crear_nota_prompt(
    titulo: str,
    tipo: str = "recurso",
    ctx: Context = None
) -> list[Message]:
    rules = (await ctx.read_resource("obsidian://vault/rules"))[0].content
    structure = (await ctx.read_resource("obsidian://vault/structure"))[0].content
    templates = (await ctx.read_resource("obsidian://templates"))[0].content

    return [Message(
        f"""Quiero crear una nota nueva en mi vault de Obsidian.

**Título/tema:** {titulo}
**Tipo:** {tipo}

---
## Reglas del vault
{rules}

---
## Estructura actual del vault
{structure}

---
## Plantillas disponibles
{templates}

---
Basándote en estas reglas y la estructura actual:
1. Decide en qué carpeta debe ir esta nota
2. Elige la plantilla más adecuada para el tipo '{tipo}'
3. Determina el nombre exacto del archivo siguiendo las convenciones
4. Llama a `create_note_from_template` con los parámetros correctos
5. Notifica por Telegram con `notify_obsidian` explicando la decisión tomada
""", role="user"
    )]

@mcp.prompt(
    name="archivar_nota",
    description="Orquesta el archivado de una nota consultando las reglas del vault.",
    tags={"archive", "workflow"}
)
async def archivar_nota_prompt(
    nota: str,
    ctx: Context = None
) -> list[Message]:
    rules = (await ctx.read_resource("obsidian://vault/rules"))[0].content
    note = (await ctx.read_resource(f"obsidian://note/{nota}"))[0].content

    return [Message(
        f"""Quiero archivar la nota '{nota}' de mi vault de Obsidian.

---
## Contenido actual de la nota
{note}

---
## Reglas del vault
{rules}

---
1. Usa `update_frontmatter` → status: archived, archived_date: {datetime.now().strftime("%Y-%m-%d")}
2. Usa `move_note` → carpeta correcta según las reglas
3. Notifica por Telegram con `notify_obsidian`
""", role="user"
    )]

@mcp.prompt(
    name="nota_diaria",
    description="Crea la nota diaria consultando la estructura del vault.",
    tags={"daily", "workflow"}
)
async def nota_diaria_prompt(ctx: Context = None) -> list[Message]:
    today = datetime.now().strftime("%Y-%m-%d")
    rules = (await ctx.read_resource("obsidian://vault/rules"))[0].content
    templates = (await ctx.read_resource("obsidian://templates"))[0].content

    return [Message(
        f"""Crea la nota diaria de hoy ({today}).

---
## Reglas del vault
{rules}

---
## Plantillas disponibles
{templates}

---
1. Elige la plantilla para notas diarias
2. Crea la nota con `create_note_from_template` en la carpeta indicada por las reglas
3. Notifica por Telegram con `notify_obsidian`
""", role="user"
    )]