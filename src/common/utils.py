import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import os
from pathlib import Path

def ensure_directory(path: str) -> None:
    """Ensure that a directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)

def format_json(obj: Any) -> str:
    """Format an object as a pretty JSON string."""
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)

def current_timestamp() -> str:
    """Get current timestamp as an ISO 8601 string."""
    return datetime.now().isoformat()

