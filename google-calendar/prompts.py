"""
Prompts predefinidos para Google Calendar MCP

Este módulo contiene workflows automatizados para el agente.
"""


def register_prompts(mcp):
    """
    Registra todos los prompts del Google Calendar MCP.
    
    Args:
        mcp: Instancia de FastMCP
    """
    
    @mcp.prompt("schedule_from_notion")
    def schedule_from_notion_prompt(task: str, deadline: str) -> str:
        """
        Planifica automáticamente una tarea de Notion en el calendario.
        
        Args:
            task: Nombre de la tarea
            deadline: Fecha límite de la tarea
            
        Returns:
            Instrucciones para el agente
        """
        return f"""
Tienes esta tarea pendiente de Notion:
- Tarea: {task}
- Deadline: {deadline}

Pasos a seguir:
1. Usa find_free_slots para encontrar huecos disponibles antes del deadline
2. Elige el hueco más adecuado considerando:
   - Duración estimada de la tarea
   - Proximidad al deadline
   - Horario más productivo
3. Crea el evento con create_event
4. Notifica por Telegram con notify_calendar explicando por qué elegiste ese hueco
"""