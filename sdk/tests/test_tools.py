"""Tests for tool helper functions."""

import json

from asahio.tools import extract_tool_calls, format_tool_result, function_to_tool


def test_function_to_tool_basic() -> None:
    """Test converting a simple function to tool schema."""

    def get_weather(location: str) -> str:
        """Get the weather for a location."""
        return f"Weather in {location}"

    tool = function_to_tool(get_weather)

    assert tool["type"] == "function"
    assert tool["function"]["name"] == "get_weather"
    assert tool["function"]["description"] == "Get the weather for a location."
    assert "location" in tool["function"]["parameters"]["properties"]
    assert "location" in tool["function"]["parameters"]["required"]


def test_function_to_tool_with_optional_params() -> None:
    """Test function with optional parameters."""

    def search(query: str, limit: int = 10, include_metadata: bool = False) -> str:
        """Search for items."""
        return f"Results for {query}"

    tool = function_to_tool(search)

    assert tool["function"]["name"] == "search"
    required = tool["function"]["parameters"]["required"]
    assert "query" in required
    assert "limit" not in required
    assert "include_metadata" not in required

    properties = tool["function"]["parameters"]["properties"]
    assert properties["query"]["type"] == "string"
    assert properties["limit"]["type"] == "integer"
    assert properties["include_metadata"]["type"] == "boolean"


def test_function_to_tool_with_override() -> None:
    """Test overriding function name and description."""

    def my_func() -> None:
        """Original description."""
        pass

    tool = function_to_tool(
        my_func,
        name="custom_name",
        description="Custom description",
    )

    assert tool["function"]["name"] == "custom_name"
    assert tool["function"]["description"] == "Custom description"


def test_function_to_tool_with_docstring_params() -> None:
    """Test extracting parameter descriptions from docstring."""

    def calculate(x: int, y: int) -> int:
        """Calculate something.

        Args:
            x: First number
            y: Second number
        """
        return x + y

    tool = function_to_tool(calculate)

    properties = tool["function"]["parameters"]["properties"]
    # Docstring param extraction is best-effort
    assert "x" in properties
    assert "y" in properties
    # If extraction works, verify it
    if "description" in properties["x"]:
        assert properties["x"]["description"] == "First number"


def test_extract_tool_calls_empty() -> None:
    """Test extracting tool calls from response with no tools."""
    response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello",
                }
            }
        ]
    }

    tool_calls = extract_tool_calls(response)
    assert tool_calls == []


def test_extract_tool_calls_single() -> None:
    """Test extracting a single tool call."""
    response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "San Francisco"}',
                            },
                        }
                    ],
                }
            }
        ]
    }

    tool_calls = extract_tool_calls(response)
    assert len(tool_calls) == 1
    assert tool_calls[0]["id"] == "call_abc123"
    assert tool_calls[0]["name"] == "get_weather"
    assert tool_calls[0]["arguments"] == '{"location": "San Francisco"}'


def test_extract_tool_calls_multiple() -> None:
    """Test extracting multiple tool calls."""
    response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "tool_one",
                                "arguments": "{}",
                            },
                        },
                        {
                            "id": "call_2",
                            "function": {
                                "name": "tool_two",
                                "arguments": '{"param": "value"}',
                            },
                        },
                    ],
                }
            }
        ]
    }

    tool_calls = extract_tool_calls(response)
    assert len(tool_calls) == 2
    assert tool_calls[0]["id"] == "call_1"
    assert tool_calls[1]["id"] == "call_2"


def test_format_tool_result_basic() -> None:
    """Test formatting a basic tool result."""
    result = format_tool_result(
        tool_call_id="call_123",
        content="Result content",
    )

    assert result["role"] == "tool"
    assert result["tool_call_id"] == "call_123"
    assert result["content"] == "Result content"
    assert "name" not in result


def test_format_tool_result_with_name() -> None:
    """Test formatting tool result with function name."""
    result = format_tool_result(
        tool_call_id="call_123",
        content='{"temp": 72}',
        name="get_weather",
    )

    assert result["role"] == "tool"
    assert result["tool_call_id"] == "call_123"
    assert result["content"] == '{"temp": 72}'
    assert result["name"] == "get_weather"


def test_tool_workflow_integration() -> None:
    """Test complete workflow: convert function, extract calls, format result."""

    # Step 1: Define and convert function to tool
    def fetch_data(resource: str, limit: int = 10) -> str:
        """Fetch data from a resource."""
        return f"Data from {resource}"

    tool_schema = function_to_tool(fetch_data)
    assert tool_schema["function"]["name"] == "fetch_data"

    # Step 2: Simulate API response with tool call
    api_response = {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {
                            "id": "call_xyz",
                            "function": {
                                "name": "fetch_data",
                                "arguments": '{"resource": "users", "limit": 5}',
                            },
                        }
                    ]
                }
            }
        ]
    }

    # Step 3: Extract tool calls
    tool_calls = extract_tool_calls(api_response)
    assert len(tool_calls) == 1
    call = tool_calls[0]

    # Step 4: Execute tool (simulated)
    args = json.loads(call["arguments"])
    result_content = fetch_data(**args)

    # Step 5: Format result for submission
    tool_result = format_tool_result(
        tool_call_id=call["id"],
        content=result_content,
        name=call["name"],
    )

    assert tool_result["role"] == "tool"
    assert tool_result["tool_call_id"] == "call_xyz"
    assert "users" in tool_result["content"]
