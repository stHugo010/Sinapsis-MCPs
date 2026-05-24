"""
core/search.py
Búsqueda en Notion
"""

import requests
from typing import Dict, Any, Optional

from ..config import get_config
from ..utils import validate_notion_id
from ..constants import SEARCH_LIMIT_DEFAULT


def search_notion(
    query: str = "",
    filter_type: Optional[str] = None,
    limit: int = SEARCH_LIMIT_DEFAULT,
) -> Dict[str, Any]:
    """
    Busca páginas y bases de datos en Notion.
    
    Args:
        query: Texto a buscar (vacío = devolver todo)
        filter_type: "page" o "database" para filtrar resultados
        limit: Número máximo de resultados
    
    Returns:
        Dict con resultados de búsqueda
    """
    config = get_config()
    
    headers = {
        "Authorization": f"Bearer {config.api_token}",
        "Notion-Version": config.api_version,
        "Content-Type": "application/json",
    }
    
    payload: Dict[str, Any] = {
        "page_size": limit,
    }
    
    if query:
        payload["query"] = query
    
    if filter_type:
        payload["filter"] = {"property": "object", "value": filter_type}
    
    try:
        response = requests.post(
            "https://api.notion.com/v1/search",
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
            "hint": "Verifica tu NOTION_API_TOKEN y la conexión a internet",
        }