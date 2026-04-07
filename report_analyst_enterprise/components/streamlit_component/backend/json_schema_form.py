"""
Streamlit custom component backend for JSON Schema form.

This creates a proper Streamlit custom component using the framework-agnostic
web component, which internally uses React and RJSF.
"""

import json
import logging
import socket
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit.components.v1 as components

logger = logging.getLogger(__name__)

# Get the path to the frontend
_COMPONENT_DIR = Path(__file__).parent.parent / "frontend"
_RELEASE_DIR = _COMPONENT_DIR / "build"


def json_schema_form(
    schema: Dict[str, Any],
    ui_schema: Optional[Dict[str, Any]] = None,
    form_data: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
    height: int = 600,
) -> Optional[Dict[str, Any]]:
    """
    Render a JSON Schema form in Streamlit using a custom component.
    
    Args:
        schema: JSON Schema object defining the form structure
        ui_schema: Optional UI Schema for customizing form appearance
        form_data: Optional initial form data
        key: Optional key for Streamlit component (for state management)
        height: Height of the component in pixels
        
    Returns:
        Dictionary with form data if form was submitted, None otherwise
    """
    # Check for dev server availability (prefer dev server for hot reload)
    dev_server_port = None
    dev_server_available = False
    
    # Check common dev server ports
    for port in [3001, 3002, 3003]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                dev_server_port = port
                dev_server_available = True
                break
        except:
            pass
    
    if dev_server_available:
        # Use dev server (hot reload)
        logger.info(f"Using JSON Schema form component from dev server (http://localhost:{dev_server_port})")
        component = components.declare_component(
            "json_schema_form",
            url=f"http://localhost:{dev_server_port}",
        )
    elif _RELEASE_DIR.exists() and any(_RELEASE_DIR.iterdir()):
        # Use built component
        logger.info(f"Using JSON Schema form component from build: {_RELEASE_DIR}")
        component = components.declare_component(
            "json_schema_form",
            path=str(_RELEASE_DIR),
        )
    else:
        # No build and no dev server - show helpful error
        logger.warning(
            f"JSON Schema form component not built and dev server not running.\n"
            f"To build the component, run:\n"
            f"  cd {_COMPONENT_DIR}\n"
            f"  npm install\n"
            f"  npm run build\n"
            f"Or for development, start the dev server:\n"
            f"  cd {_COMPONENT_DIR}\n"
            f"  npm start (in a separate terminal)"
        )
        # Still try to declare component - Streamlit will show its own error
        component = components.declare_component(
            "json_schema_form",
            url="http://localhost:3001",
        )
    
    # Render component and get result
    result = component(
        schema=json.dumps(schema),
        uiSchema=json.dumps(ui_schema or {}),
        formData=json.dumps(form_data or {}),
        key=key,
        height=height,
    )
    
    # Parse result if it's a string
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            pass
    
    return result

