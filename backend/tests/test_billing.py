from httpx import AsyncClient


def _auth_header(raw_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {raw_key}"}


async def test_billing_endpoints(
    client: AsyncClient,
    seed_org: dict[str, object],
) -> None:
    raw_key = seed_org["raw_key"]  # type: ignore[index]

    plans_resp = await client.get("/billing/plans", headers=_auth_header(raw_key))
    assert plans_resp.status_code == 200
    plans = plans_resp.json()
    assert any(plan["id"] == "free" for plan in plans)
    assert any(plan["id"] == "pro" for plan in plans)

    subscription_resp = await client.get("/billing/subscription", headers=_auth_header(raw_key))
    assert subscription_resp.status_code == 200
    subscription = subscription_resp.json()
    assert subscription["plan"] == "free"

    usage_resp = await client.get("/billing/usage", headers=_auth_header(raw_key))
    assert usage_resp.status_code == 200
    usage = usage_resp.json()
    assert usage["requests_used"] >= 0

    checkout_resp = await client.post(
        "/billing/checkout",
        json={
            "plan": "pro",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        },
        headers=_auth_header(raw_key),
    )
    assert checkout_resp.status_code == 200
    checkout = checkout_resp.json()
    assert "checkout_url" in checkout
