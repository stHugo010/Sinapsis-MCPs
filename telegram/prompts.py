"""
Prompts predefinidos para Telegram MCP

Este módulo contiene workflows automatizados que el agente puede ejecutar.
"""


def register_prompts(mcp):
    """
    Registra todos los prompts del Telegram MCP.
    
    Args:
        mcp: Instancia de FastMCP
    """
    
    @mcp.prompt("daily_report")
    def daily_report_prompt() -> str:
        """
        Instrucciones para que el agente genere y envíe el resumen diario.
        
        Este prompt guía al agente para recopilar información de todos los MCPs
        y crear un resumen consolidado del día.
        
        Returns:
            Template de instrucciones para el agente
        """
        return """
Genera un resumen del día usando send_summary con:
- Notas creadas o modificadas en Obsidian
- Tareas completadas o creadas en Notion  
- Eventos añadidos al calendario
- Alertas del sistema si las hay

Título: 'Resumen del día · DD/MM/YYYY'
Sé conciso, máximo 6 bullets.
"""