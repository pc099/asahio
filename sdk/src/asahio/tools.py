"""Tool use helpers for the ASAHIO Python SDK."""

from __future__ import annotations

import inspect
from typing import Any, Callable, Optional, get_type_hints


def function_to_tool(
    func: Callable,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> dict[str, Any]:
    """Convert a Python function to OpenAI tool schema format.

    Args:
        func: Python function to convert
        name: Optional override for function name
        description: Optional override for function description

    Returns:
        Tool schema dict compatible with OpenAI/Anthropic tool format

    Example:
        >>> def get_weather(location: str, unit: str = "celsius") -> str:
        ...     '''Get the weather for a location.'''
        ...     return f"Weather in {location}"
        >>> tool = function_to_tool(get_weather)
        >>> tool["function"]["name"]
        'get_weather'
    """
    func_name = name or func.__name__
    func_desc = description or (inspect.getdoc(func) or "No description provided")

    # Get function signature
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    # Build parameters schema
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        param_type = type_hints.get(param_name, Any)
        param_schema = _python_type_to_json_schema(param_type)

        # Try to extract parameter description from docstring
        param_desc = _extract_param_description(func, param_name)
        if param_desc:
            param_schema["description"] = param_desc

        properties[param_name] = param_schema

        # Mark as required if no default value
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "function",
        "function": {
            "name": func_name,
            "description": func_desc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def _python_type_to_json_schema(py_type: Any) -> dict[str, Any]:
    """Convert Python type hint to JSON schema type."""
    # Handle Optional types
    origin = getattr(py_type, "__origin__", None)
    if origin is type(None):
        return {"type": "null"}

    # Handle Union types (including Optional)
    if origin is Union:
        args = py_type.__args__
        # If Union with None, treat as optional
        if type(None) in args:
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                return _python_type_to_json_schema(non_none[0])
        return {"type": "string"}  # Fallback for complex unions

    # Handle list/List
    if origin is list:
        return {"type": "array", "items": {"type": "string"}}

    # Handle dict/Dict
    if origin is dict:
        return {"type": "object"}

    # Map basic types
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    actual_type = py_type
    if isinstance(py_type, type):
        actual_type = py_type
    else:
        actual_type = str  # Fallback

    json_type = type_map.get(actual_type, "string")
    return {"type": json_type}


def _extract_param_description(func: Callable, param_name: str) -> Optional[str]:
    """Extract parameter description from function docstring (Google style)."""
    doc = inspect.getdoc(func)
    if not doc:
        return None

    # Simple extraction for Google-style docstrings
    lines = doc.split("\n")
    in_args_section = False
    for line in lines:
        stripped = line.strip()
        if stripped in ("Args:", "Arguments:", "Parameters:"):
            in_args_section = True
            continue
        if in_args_section:
            if stripped.startswith(f"{param_name}:"):
                return stripped[len(param_name) + 1 :].strip()
            if stripped and not stripped.startswith(" ") and ":" in stripped:
                # Moved to next parameter or section
                break
    return None


def extract_tool_calls(response: dict) -> list[dict[str, Any]]:
    """Extract tool calls from a chat completion response.

    Args:
        response: Chat completion response dict

    Returns:
        List of tool call dicts with keys: id, name, arguments

    Example:
        >>> response = {"choices": [{"message": {"tool_calls": [...]}}]}
        >>> calls = extract_tool_calls(response)
        >>> calls[0]["name"]
        'get_weather'
    """
    tool_calls = []

    choices = response.get("choices", [])
    if not choices:
        return tool_calls

    message = choices[0].get("message", {})
    raw_tool_calls = message.get("tool_calls", [])

    for tc in raw_tool_calls:
        tool_calls.append(
            {
                "id": tc.get("id"),
                "name": tc.get("function", {}).get("name"),
                "arguments": tc.get("function", {}).get("arguments", "{}"),
            }
        )

    return tool_calls


def format_tool_result(
    *,
    tool_call_id: str,
    content: str,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """Format a tool result for submission to the API.

    Args:
        tool_call_id: ID of the tool call being responded to
        content: Result content as string
        name: Optional tool name

    Returns:
        Message dict formatted as a tool result

    Example:
        >>> result = format_tool_result(
        ...     tool_call_id="call_123",
        ...     content='{"temp": 72, "condition": "sunny"}',
        ...     name="get_weather"
        ... )
        >>> result["role"]
        'tool'
    """
    msg: dict[str, Any] = {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }
    if name is not None:
        msg["name"] = name
    return msg


# Import Union for type checking
try:
    from typing import Union
except ImportError:
    Union = None  # type: ignore
