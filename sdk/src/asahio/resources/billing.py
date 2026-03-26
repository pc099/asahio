"""Billing resource for the ASAHIO Python SDK."""

from __future__ import annotations

from typing import Optional

from asahio.resources import AsyncResource, SyncResource
from asahio.types.billing import BillingPlan, BillingUsage, Subscription


class Billing(SyncResource):
    """Sync billing resource."""

    def get_subscription(self) -> Subscription:
        """Get current subscription."""
        response = self._client.get("/billing/subscription")
        return Subscription.from_dict(response.json())

    def list_plans(self) -> list[BillingPlan]:
        """List available billing plans."""
        response = self._client.get("/billing/plans")
        data = response.json()
        return [BillingPlan.from_dict(p) for p in data.get("data", [])]

    def get_usage(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> BillingUsage:
        """Get billing usage for a period."""
        params = {}
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date

        response = self._client.get("/billing/usage", params=params if params else None)
        return BillingUsage.from_dict(response.json())

    def update_subscription(self, *, plan_id: str) -> Subscription:
        """Update subscription plan."""
        body = {"plan_id": plan_id}
        response = self._client.post("/billing/subscription/update", json=body)
        return Subscription.from_dict(response.json())


class AsyncBilling(AsyncResource):
    """Async billing resource."""

    async def get_subscription(self) -> Subscription:
        """Get current subscription."""
        response = await self._client.get("/billing/subscription")
        return Subscription.from_dict(response.json())

    async def list_plans(self) -> list[BillingPlan]:
        """List available billing plans."""
        response = await self._client.get("/billing/plans")
        data = response.json()
        return [BillingPlan.from_dict(p) for p in data.get("data", [])]

    async def get_usage(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> BillingUsage:
        """Get billing usage for a period."""
        params = {}
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date

        response = await self._client.get("/billing/usage", params=params if params else None)
        return BillingUsage.from_dict(response.json())

    async def update_subscription(self, *, plan_id: str) -> Subscription:
        """Update subscription plan."""
        body = {"plan_id": plan_id}
        response = await self._client.post("/billing/subscription/update", json=body)
        return Subscription.from_dict(response.json())
