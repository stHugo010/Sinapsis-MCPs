"""
utils/formatters.py
Formateadores de datos para respuestas consistentes
"""

import json
from typing import Any, Dict


def format_json_response(data: Dict[str, Any], indent: int = 2) -> str:
    """Formatea respuesta como JSON con formato consistente"""
    return json.dumps(data, indent=indent, ensure_ascii=False)


def format_error(error: str, hint: str = "") -> str:
    """Formatea mensaje de error"""
    response: Dict[str, Any] = {"error": error}
    if hint:
        response["hint"] = hint
    return format_json_response(response)


def format_success(message: str, data: Dict[str, Any] = None) -> str:
    """Formatea mensaje de éxito"""
    response: Dict[str, Any] = {"success": True, "message": message}
    if data:
        response.update(data)
    return format_json_response(response)


def format_blocked_operation(reason: str) -> str:
    """Formatea respuesta de operación bloqueada"""
    return format_json_response({
        "success": False,
        "blocked": True,
        "reason": reason,
        "message": f"Operación bloqueada por el guardian de seguridad: {reason}",
    })