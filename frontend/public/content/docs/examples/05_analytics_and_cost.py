"""
Example 5: Analytics and Cost Monitoring

This example demonstrates:
- Viewing cost analytics
- Model usage breakdown
- Cache performance metrics
- Savings analysis
"""

from asahio import Asahio
from datetime import datetime, timedelta

client = Asahio()

# Get overview analytics
print("=" * 60)
print("ANALYTICS OVERVIEW")
print("=" * 60)

# Calculate date range (last 30 days)
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

overview = client.analytics.overview(
    start_date=start_date.strftime("%Y-%m-%d"),
    end_date=end_date.strftime("%Y-%m-%d"),
)

print(f"Period: {start_date.date()} to {end_date.date()}\n")
print(f"Total calls: {overview.total_calls:,}")
print(f"Total cost: ${overview.total_cost:.2f}")
print(f"Total savings: ${overview.total_savings:.2f}")
print(f"Avg cost per call: ${overview.avg_cost_per_call:.4f}")
print(f"Cache hit rate: {overview.cache_hit_rate:.1%}")
print(f"Avg latency: {overview.avg_latency_ms:.0f}ms")

# Model usage breakdown
print("\n" + "=" * 60)
print("MODEL USAGE BREAKDOWN")
print("=" * 60)

breakdown = client.analytics.model_breakdown(
    start_date=start_date.strftime("%Y-%m-%d"),
    end_date=end_date.strftime("%Y-%m-%d"),
)

print(f"{'Model':<25} {'Calls':<10} {'Cost':<12} {'Avg Latency':<15} {'Success Rate':<15}")
print("-" * 80)

for model in breakdown:
    print(f"{model.model_name:<25} {model.call_count:<10,} ${model.total_cost:<11.2f} {model.avg_latency_ms:<14.0f}ms {model.success_rate:<14.1%}")

# Cache performance
print("\n" + "=" * 60)
print("CACHE PERFORMANCE")
print("=" * 60)

cache = client.analytics.cache_performance()

print(f"Overall hit rate: {cache.overall_hit_rate:.1%}")
print(f"Tier 1 (exact) hits: {cache.tier1_hits:,}")
print(f"Tier 2 (semantic) hits: {cache.tier2_hits:,}")
print(f"Total cache hits: {cache.total_hits:,}")
print(f"Total requests: {cache.total_requests:,}")
print(f"Avg cache latency: {cache.avg_cache_latency_ms:.1f}ms")
print(f"Savings from cache: ${cache.savings_from_cache_usd:.2f}")

# Savings breakdown
print("\n" + "=" * 60)
print("SAVINGS BREAKDOWN")
print("=" * 60)

savings = client.analytics.savings()

total_savings = sum(s.savings_usd for s in savings)
print(f"Total savings: ${total_savings:.2f}\n")

for source in savings:
    print(f"{source.source.replace('_', ' ').title():<30} ${source.savings_usd:<10.2f} {source.percentage_of_total:>6.1f}%")

# Agent-specific analytics
print("\n" + "=" * 60)
print("PER-AGENT ANALYTICS")
print("=" * 60)

# List agents
agents = client.agents.list()

for agent in agents[:3]:  # Show first 3 agents
    print(f"\nAgent: {agent.name}")

    # Get stats
    stats = client.agents.stats(agent.id)
    print(f"  Total calls: {stats.total_calls:,}")
    print(f"  Cache hit rate: {stats.cache_hit_rate:.1%}")
    print(f"  Avg latency: {stats.avg_latency_ms:.0f}ms" if stats.avg_latency_ms else "  Avg latency: N/A")

    # Get interventions
    try:
        intervention_stats = client.interventions.get_stats(agent_id=agent.id)
        print(f"  Intervention rate: {intervention_stats.intervention_rate:.1%}")
        print(f"  Augmented: {intervention_stats.augmented_count}")
        print(f"  Rerouted: {intervention_stats.rerouted_count}")
        print(f"  Blocked: {intervention_stats.blocked_count}")
    except Exception:
        print(f"  Interventions: N/A")

# Fleet-wide intervention overview
print("\n" + "=" * 60)
print("FLEET INTERVENTION OVERVIEW")
print("=" * 60)

try:
    fleet = client.interventions.fleet_overview()
    print(f"Total agents: {fleet.total_agents}")
    print(f"24h interventions: {fleet.total_interventions_24h:,}")
    print(f"Avg risk score: {fleet.avg_risk_score:.2f}")
    print(f"Agents in autonomous mode: {fleet.agents_in_autonomous_mode}")

    if fleet.high_risk_agents:
        print("\nHigh-risk agents:")
        for agent_info in fleet.high_risk_agents[:3]:
            print(f"  - {agent_info['agent_id']}: risk {agent_info['risk_score']:.2f}")
except Exception as e:
    print(f"Fleet overview not available: {e}")

# Billing information
print("\n" + "=" * 60)
print("BILLING")
print("=" * 60)

subscription = client.billing.get_subscription()
print(f"Current plan: {subscription.plan_id}")
print(f"Status: {subscription.status}")
print(f"Period: {subscription.current_period_start} to {subscription.current_period_end}")

usage = client.billing.get_usage()
print(f"\nUsage this period:")
print(f"  Total calls: {usage.total_calls:,}")
print(f"  Included calls: {usage.included_calls:,}")
print(f"  Overage calls: {usage.overage_calls:,}")
print(f"  Estimated cost: ${usage.estimated_cost:.2f}")

if usage.overage_calls > 0:
    print(f"\n⚠️  Warning: You have {usage.overage_calls:,} overage calls")

client.close()
