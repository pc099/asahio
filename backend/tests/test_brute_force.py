"""Tests for brute force protection middleware."""

import pytest

from app.middleware.brute_force import (
    MAX_FAILURES,
    get_lockout_seconds,
    record_auth_failure,
    record_auth_success,
    reset_tracker,
)


@pytest.fixture(autouse=True)
def _clean_tracker():
    """Reset failure tracker before each test."""
    reset_tracker()
    yield
    reset_tracker()


class TestBruteForceTracking:
    """Tests for the brute force tracking logic."""

    def test_no_lockout_below_threshold(self) -> None:
        ip = "192.168.1.1"
        for _ in range(MAX_FAILURES - 1):
            record_auth_failure(ip)
        assert get_lockout_seconds(ip) is None

    def test_lockout_at_threshold(self) -> None:
        ip = "10.0.0.1"
        for _ in range(MAX_FAILURES):
            record_auth_failure(ip)
        remaining = get_lockout_seconds(ip)
        assert remaining is not None
        assert remaining > 0

    def test_success_resets_tracker(self) -> None:
        ip = "10.0.0.2"
        for _ in range(MAX_FAILURES):
            record_auth_failure(ip)
        record_auth_success(ip)
        assert get_lockout_seconds(ip) is None

    def test_lockout_duration_increases(self) -> None:
        ip = "172.16.0.1"
        for _ in range(MAX_FAILURES + 3):
            record_auth_failure(ip)
        remaining = get_lockout_seconds(ip)
        assert remaining is not None
        # With 3 excess failures: 2^3 = 8 seconds lockout
        assert remaining <= 8.0

    def test_no_lockout_for_unknown_ip(self) -> None:
        assert get_lockout_seconds("1.2.3.4") is None

    def test_reset_clears_all(self) -> None:
        for _ in range(MAX_FAILURES):
            record_auth_failure("1.1.1.1")
        reset_tracker()
        assert get_lockout_seconds("1.1.1.1") is None
