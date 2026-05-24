"""
utils/validators.py
Validadores de datos
"""

import re
from typing import Union


def validate_notion_id(notion_id: str) -> bool:
    """
    Valida formato de ID de Notion.
    
    Formato esperado: 32 caracteres hexadecimales con o sin guiones
    Ejemplo: 1234567890abcdef1234567890abcdef
    O: 12345678-90ab-cdef-1234-567890abcdef
    """
    # Remover guiones para validar
    clean_id = notion_id.replace("-", "")
    
    # Debe ser exactamente 32 caracteres hexadecimales
    if len(clean_id) != 32:
        return False
    
    # Verificar que solo contenga caracteres hexadecimales
    return bool(re.match(r'^[0-9a-fA-F]{32}$', clean_id))


def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """Limita un valor entre min y max"""
    return max(min_val, min(max_val, value))