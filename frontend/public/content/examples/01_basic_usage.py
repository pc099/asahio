"""
Example 1: Basic ASAHIO Usage

This example demonstrates the basics of using ASAHIO:
- Initializing the client
- Making a simple chat completion request
- Accessing response metadata (cost, savings, model used)
"""

from asahio import Asahio

# Initialize client (reads from ASAHIO_API_KEY env var)
client = Asahio()

# Make a simple request
response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Explain quantum computing in simple terms"}
    ],
)

# Access the response
print("=" * 60)
print("RESPONSE")
print("=" * 60)
print(response.choices[0].message.content)

# Access ASAHIO metadata
print("\n" + "=" * 60)
print("ASAHIO METADATA")
print("=" * 60)
metadata = response.asahio
print(f"Request ID: {metadata.request_id}")
print(f"Model requested: {metadata.model_requested or 'AUTO'}")
print(f"Model used: {metadata.model_used}")
print(f"Provider: {metadata.provider}")
print(f"Routing mode: {metadata.routing_mode}")
print(f"Cache hit: {metadata.cache_hit}")
print(f"Cache tier: {metadata.cache_tier or 'N/A'}")

# Cost analysis
print("\n" + "=" * 60)
print("COST ANALYSIS")
print("=" * 60)
print(f"Cost without ASAHIO: ${metadata.cost_without_asahio:.4f}")
print(f"Cost with ASAHIO: ${metadata.cost_with_asahio:.4f}")
print(f"Savings: ${metadata.savings_usd:.4f} ({metadata.savings_pct:.1f}%)")

# Risk scoring
print("\n" + "=" * 60)
print("RISK ANALYSIS")
print("=" * 60)
print(f"Risk score: {metadata.risk_score:.2f}")
print(f"Intervention level: {metadata.intervention_level}")

# Run the same query again to see caching in action
print("\n" + "=" * 60)
print("SECOND REQUEST (TESTING CACHE)")
print("=" * 60)
response2 = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Explain quantum computing in simple terms"}
    ],
)

print(f"Cache hit: {response2.asahio.cache_hit}")
print(f"Cache tier: {response2.asahio.cache_tier}")
print(f"Response time: ~2ms (from cache)")

client.close()
