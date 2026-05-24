"""
core/page.py
Gestión de páginas de Notion
"""

import requests
from typing import Dict, Any, Optional

from ..config import get_config
from ..utils import validate_notion_id


def get_page_content(page_id: str) -> Dict[str, Any]:
    """
    Obtiene el contenido de una página de Notion.
    
    Args:
        page_id: ID de la página
    
    Returns:
        Dict con metadatos y bloques de la página
    """
    if not validate_notion_id(page_id):
        return {
            "success": False,
            "error": "ID de página inválido",
            "hint": "El ID debe tener 32 caracteres hexadecimales",
        }
    
    config = get_config()
    
    headers = {
        "Authorization": f"Bearer {config.api_token}",
        "Notion-Version": config.api_version,
    }
    
    try:
        # Obtener metadatos de la página
        page_response = requests.get(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=headers,
            timeout=10,
        )
        page_response.raise_for_status()
        page_data = page_response.json()
        
        # Obtener bloques de contenido
        blocks_response = requests.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            timeout=10,
        )
        blocks_response.raise_for_status()
        blocks_data = blocks_response.json()
        
        return {
            "success": True,
            "page": {
                "id": page_data.get("id"),
                "created_time": page_data.get("created_time"),
                "last_edited_time": page_data.get("last_edited_time"),
                "properties": page_data.get("properties", {}),
            },
            "blocks": blocks_data.get("results", []),
            "total_blocks": len(blocks_data.get("results", [])),
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
        }


def create_page(
    parent_id: str,
    title: str,
    content: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Crea una nueva página en Notion.
    
    Args:
        parent_id: ID de la página padre o database
        title: Título de la nueva página
        content: Contenido opcional (texto)
    
    Returns:
        Dict con información de la página creada
    """
    if not validate_notion_id(parent_id):
        return {
            "success": False,
            "error": "ID de padre inválido",
        }
    
    config = get_config()
    
    headers = {
        "Authorization": f"Bearer {config.api_token}",
        "Notion-Version": config.api_version,
        "Content-Type": "application/json",
    }
    
    # Payload básico
    payload: Dict[str, Any] = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": {
                "title": [
                    {
                        "text": {"content": title}
                    }
                ]
            }
        },
    }
    
    # Añadir contenido si se proporciona
    if content:
        payload["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": content}
                        }
                    ]
                }
            }
        ]
    
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


def append_to_page(
    page_id: str,
    text: str,
    block_type: str = "paragraph",
) -> Dict[str, Any]:
    """
    Añade un bloque de texto a una página existente.
    
    Args:
        page_id: ID de la página
        text: Texto a añadir
        block_type: Tipo de bloque ("paragraph", "heading_1", etc.)
    
    Returns:
        Dict con resultado de la operación
    """
    if not validate_notion_id(page_id):
        return {
            "success": False,
            "error": "ID de página inválido",
        }
    
    config = get_config()
    
    headers = {
        "Authorization": f"Bearer {config.api_token}",
        "Notion-Version": config.api_version,
        "Content-Type": "application/json",
    }
    
    # Construir bloque según tipo
    block: Dict[str, Any] = {
        "object": "block",
        "type": block_type,
        block_type: {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": text}
                }
            ]
        }
    }
    
    payload = {
        "children": [block]
    }
    
    try:
        response = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "blocks_added": len(data.get("results", [])),
            "message": f"Bloque de tipo '{block_type}' añadido correctamente",
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
        }