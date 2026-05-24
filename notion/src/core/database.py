"""
core/database.py
Gestión de bases de datos de Notion
"""

import requests
from typing import Dict, Any

from ..config import get_config
from ..utils import validate_notion_id
from ..constants import PAGE_SIZE_DEFAULT


def list_database_items(
    database_id: str,
    page_size: int = PAGE_SIZE_DEFAULT,
) -> Dict[str, Any]:
    """
    Lista las entradas de una base de datos de Notion.
    
    Args:
        database_id: ID de la base de datos
        page_size: Número de resultados por página
    
    Returns:
        Dict con entradas de la base de datos
    """
    if not validate_notion_id(database_id):
        return {
            "success": False,
            "error": "ID de database inválido",
        }
    
    config = get_config()
    
    headers = {
        "Authorization": f"Bearer {config.api_token}",
        "Notion-Version": config.api_version,
        "Content-Type": "application/json",
    }
    
    payload = {
        "page_size": page_size,
    }
    
    try:
        response = requests.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers=headers,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "results": data.get("results", []),
            "total": len(data.get("results", [])),
            "has_more": data.get("has_more", False),
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
        }


def create_database_entry(
    database_id: str,
    properties: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Crea una nueva entrada en una base de datos.
    
    Args:
        database_id: ID de la base de datos
        properties: Propiedades de la nueva entrada
    
    Returns:
        Dict con información de la entrada creada
    """
    if not validate_notion_id(database_id):
        return {
            "success": False,
            "error": "ID de database inválido",
        }
    
    config = get_config()
    
    headers = {
        "Authorization": f"Bearer {config.api_token}",
        "Notion-Version": config.api_version,
        "Content-Type": "application/json",
    }
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }
    
    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "page_id": data.get("id"),
            "url": data.get("url"),
            "created_time": data.get("created_time"),
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
        }