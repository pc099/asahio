"""
Example 3: Tool Use (Function Calling)

This example demonstrates:
- Converting Python functions to tools
- Making requests with tools
- Extracting and executing tool calls
- Submitting tool results back to the model
"""

import json
from asahio import Asahio
from asahio.tools import function_to_tool, extract_tool_calls, format_tool_result

client = Asahio()

# Define tools as Python functions
def get_weather(location: str, unit: str = "celsius") -> str:
    """Get the current weather for a location.

    Args:
        location: City name or location
        unit: Temperature unit (celsius or fahrenheit)
    """
    # In a real app, you'd call a weather API here
    return json.dumps({
        "location": location,
        "temperature": 22,
        "unit": unit,
        "condition": "sunny",
        "humidity": 65
    })


def calculate(operation: str, a: float, b: float) -> str:
    """Perform a mathematical calculation.

    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        a: First number
        b: Second number
    """
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "Error: Division by zero"
    }
    result = operations.get(operation, "Error: Unknown operation")
    return json.dumps({"operation": operation, "result": result})


# Convert functions to OpenAI-compatible tool schemas
weather_tool = function_to_tool(get_weather)
calc_tool = function_to_tool(calculate)

print("=" * 60)
print("TOOL DEFINITIONS")
print("=" * 60)
print(f"Weather tool: {weather_tool['function']['name']}")
print(f"  Description: {weather_tool['function']['description']}")
print(f"  Parameters: {list(weather_tool['function']['parameters']['properties'].keys())}")

print(f"\nCalculator tool: {calc_tool['function']['name']}")
print(f"  Description: {calc_tool['function']['description']}")
print(f"  Parameters: {list(calc_tool['function']['parameters']['properties'].keys())}")

# Make a request with tools
print("\n" + "=" * 60)
print("REQUEST WITH TOOLS")
print("=" * 60)

conversation = [
    {"role": "user", "content": "What's the weather in San Francisco and what's 15 * 7?"}
]

response = client.chat.completions.create(
    messages=conversation,
    tools=[weather_tool, calc_tool],
    tool_choice="auto",  # Let the model decide when to use tools
)

print(f"Model response: {response.choices[0].message.content or '(No text, calling tools)'}")
print(f"Finish reason: {response.choices[0].finish_reason}")

# Check if tools were called
if response.choices[0].finish_reason == "tool_calls":
    print("\n" + "=" * 60)
    print("TOOL CALLS DETECTED")
    print("=" * 60)

    # Extract tool calls from response
    tool_calls = extract_tool_calls(response.model_dump())

    print(f"Number of tool calls: {len(tool_calls)}")

    # Execute each tool call
    tool_results = []
    for call in tool_calls:
        print(f"\nExecuting: {call['name']}")
        print(f"  Call ID: {call['id']}")
        print(f"  Arguments: {call['arguments']}")

        # Parse arguments
        args = json.loads(call['arguments'])

        # Execute the appropriate function
        if call['name'] == 'get_weather':
            result = get_weather(**args)
        elif call['name'] == 'calculate':
            result = calculate(**args)
        else:
            result = json.dumps({"error": "Unknown function"})

        print(f"  Result: {result}")

        # Format result for submission
        tool_results.append(format_tool_result(
            tool_call_id=call['id'],
            content=result,
            name=call['name']
        ))

    # Submit tool results back to the model
    print("\n" + "=" * 60)
    print("SUBMITTING TOOL RESULTS")
    print("=" * 60)

    # Add assistant's tool calls to conversation
    conversation.append(response.choices[0].message.model_dump())

    # Add tool results
    conversation.extend(tool_results)

    # Get final response
    final_response = client.chat.completions.create(
        messages=conversation,
        tools=[weather_tool, calc_tool],
    )

    print("Final response:")
    print(final_response.choices[0].message.content)

    # Check metadata
    print("\n" + "=" * 60)
    print("TOOL USAGE METADATA")
    print("=" * 60)
    print(f"Tools called: {final_response.asahio.tools_called}")
    print(f"Model used: {final_response.asahio.model_used}")
    print(f"Cost: ${final_response.asahio.cost_with_asahio:.4f}")

else:
    print("\nNo tools were called - model answered directly")
    print(response.choices[0].message.content)

client.close()
