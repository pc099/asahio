"""Tests for the dependency fingerprint builder."""

from app.services.dependency_classifier import build_dependency_fingerprint


class TestBuildDependencyFingerprint:
    """Tests for build_dependency_fingerprint."""

    def test_deterministic(self) -> None:
        fp1 = build_dependency_fingerprint(["INDEPENDENT", "PARTIAL"])
        fp2 = build_dependency_fingerprint(["INDEPENDENT", "PARTIAL"])
        assert fp1 == fp2

    def test_order_independent(self) -> None:
        fp1 = build_dependency_fingerprint(["PARTIAL", "INDEPENDENT", "DEPENDENT"])
        fp2 = build_dependency_fingerprint(["INDEPENDENT", "DEPENDENT", "PARTIAL"])
        assert fp1 == fp2

    def test_different_levels_different_hash(self) -> None:
        fp1 = build_dependency_fingerprint(["INDEPENDENT"])
        fp2 = build_dependency_fingerprint(["DEPENDENT"])
        assert fp1 != fp2

    def test_step_changes_hash(self) -> None:
        fp1 = build_dependency_fingerprint(["INDEPENDENT"], session_step=1)
        fp2 = build_dependency_fingerprint(["INDEPENDENT"], session_step=2)
        assert fp1 != fp2

    def test_returns_16_hex_chars(self) -> None:
        fp = build_dependency_fingerprint(["INDEPENDENT", "PARTIAL"], session_step=3)
        assert len(fp) == 16
        assert all(c in "0123456789abcdef" for c in fp)

    def test_empty_levels(self) -> None:
        fp = build_dependency_fingerprint([])
        assert len(fp) == 16

    def test_with_step_none(self) -> None:
        fp = build_dependency_fingerprint(["INDEPENDENT"], session_step=None)
        assert len(fp) == 16
