"""Tests for the circuit breaker, retry, and timeout service."""

import asyncio
import time

import pytest

from app.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    ProviderTimeoutError,
    RetryConfig,
    _compute_delay,
    execute_with_retry,
)


# ---------------------------------------------------------------------------
# Circuit Breaker unit tests
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    def test_starts_closed(self) -> None:
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True

    def test_opens_after_threshold_failures(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

    def test_success_resets_failure_count(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb._failure_count == 0
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

    def test_transitions_to_half_open_after_recovery(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout_seconds=0.01,  # Very short for testing
        ))
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.can_execute() is True

    def test_half_open_success_closes_circuit(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout_seconds=0.01,
        ))
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_reopens_circuit(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout_seconds=0.01,
        ))
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_half_open_limits_calls(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout_seconds=0.01,
            half_open_max_calls=1,
        ))
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.can_execute() is True
        cb._half_open_calls = 1
        assert cb.can_execute() is False

    def test_degraded_provider_lower_threshold(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=5,
            degraded_failure_threshold=2,
        ))
        cb.set_provider_health("degraded")
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_healthy_provider_restores_threshold(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=5,
            degraded_failure_threshold=2,
        ))
        cb.set_provider_health("degraded")
        assert cb._effective_threshold == 2
        cb.set_provider_health("healthy")
        assert cb._effective_threshold == 5

    def test_reset_clears_state(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    def test_recovery_remaining(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout_seconds=10.0,
        ))
        cb.record_failure()
        remaining = cb.recovery_remaining()
        assert remaining > 9.0
        assert remaining <= 10.0

    def test_recovery_remaining_zero_when_closed(self) -> None:
        cb = CircuitBreaker("test")
        assert cb.recovery_remaining() == 0.0


# ---------------------------------------------------------------------------
# Retry logic tests
# ---------------------------------------------------------------------------

class TestRetryConfig:
    def test_compute_delay_exponential(self) -> None:
        config = RetryConfig(base_delay_seconds=1.0, jitter=False)
        assert _compute_delay(0, config) == 1.0
        assert _compute_delay(1, config) == 2.0
        assert _compute_delay(2, config) == 4.0

    def test_compute_delay_capped(self) -> None:
        config = RetryConfig(base_delay_seconds=1.0, max_delay_seconds=3.0, jitter=False)
        assert _compute_delay(5, config) == 3.0

    def test_compute_delay_jitter_varies(self) -> None:
        config = RetryConfig(base_delay_seconds=1.0, jitter=True)
        delays = {_compute_delay(0, config) for _ in range(20)}
        assert len(delays) > 1  # Jitter should produce different values


# ---------------------------------------------------------------------------
# execute_with_retry tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestExecuteWithRetry:
    async def test_success_on_first_attempt(self) -> None:
        cb = CircuitBreaker("test")
        call_count = 0

        async def success():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await execute_with_retry(success, cb)
        assert result == "ok"
        assert call_count == 1
        assert cb.state == CircuitState.CLOSED

    async def test_success_on_second_attempt(self) -> None:
        cb = CircuitBreaker("test")
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("transient")
            return "ok"

        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        result = await execute_with_retry(fail_then_succeed, cb, config)
        assert result == "ok"
        assert call_count == 2

    async def test_all_retries_exhausted_opens_circuit(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))

        async def always_fail():
            raise ConnectionError("down")

        config = RetryConfig(max_attempts=2, base_delay_seconds=0.01)
        with pytest.raises(ConnectionError):
            await execute_with_retry(always_fail, cb, config)
        assert cb.state == CircuitState.OPEN

    async def test_circuit_open_raises_immediately(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        async def should_not_run():
            raise AssertionError("Should not be called")

        with pytest.raises(CircuitOpenError) as exc_info:
            await execute_with_retry(should_not_run, cb)
        assert "test" in str(exc_info.value)

    async def test_timeout_enforcement(self) -> None:
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=5))

        async def slow_call():
            await asyncio.sleep(10)
            return "should not reach"

        config = RetryConfig(max_attempts=1, base_delay_seconds=0.01)
        with pytest.raises(ProviderTimeoutError):
            await execute_with_retry(slow_call, cb, config, timeout_seconds=0.05)

    async def test_happy_path_no_overhead(self) -> None:
        """Verify circuit breaker adds negligible overhead on happy path."""
        cb = CircuitBreaker("test")

        async def instant():
            return 42

        start = time.monotonic()
        for _ in range(100):
            await execute_with_retry(instant, cb)
        elapsed = time.monotonic() - start
        # 100 calls should complete in well under 500ms
        assert elapsed < 0.5
