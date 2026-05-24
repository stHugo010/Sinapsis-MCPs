"""
utils/formatters.py
Formateadores de respuestas JSON
"""

import json
from typing import Any, Dict


def format_json_response(data: Dict[str, Any], indent: int = 2) -> str:
    """Formatea respuesta como JSON"""
    return json.dumps(data, indent=indent, ensure_ascii=False)


def format_error(error: str, hint: str = "") -> str:
    """Formatea mensaje de error"""
    response: Dict[str, Any] = {"error": error}
    if hint:
        response["hint"] = hint
    return format_json_response(response)