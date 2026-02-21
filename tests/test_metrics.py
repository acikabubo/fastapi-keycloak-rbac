"""Tests for fastapi_keycloak_rbac/metrics.py"""

import pytest
from prometheus_client import REGISTRY


def _get_counter_value(name: str, labels: dict[str, str] | None = None) -> float:
    """Helper to read a Prometheus counter value from the default registry."""
    metric = REGISTRY._names_to_collectors.get(name)
    if metric is None:
        return 0.0
    if labels:
        return metric.labels(**labels)._value.get()
    return metric._value.get()  # type: ignore[attr-defined]


def _get_sample_value(name: str, labels: dict[str, str] | None = None) -> float:
    """Read a sample value by iterating collected metrics."""
    for metric in REGISTRY.collect():
        for sample in metric.samples:
            if sample.name == name and (
                labels is None or all(sample.labels.get(k) == v for k, v in labels.items())
            ):
                return sample.value
    return 0.0


class TestRecordCacheHit:
    def test_increments_counter(self) -> None:
        from fastapi_keycloak_rbac.metrics import record_cache_hit

        before = _get_sample_value("keycloak_rbac_token_cache_hits_total")
        record_cache_hit()
        after = _get_sample_value("keycloak_rbac_token_cache_hits_total")
        assert after == before + 1


class TestRecordCacheMiss:
    def test_increments_counter(self) -> None:
        from fastapi_keycloak_rbac.metrics import record_cache_miss

        before = _get_sample_value("keycloak_rbac_token_cache_misses_total")
        record_cache_miss()
        after = _get_sample_value("keycloak_rbac_token_cache_misses_total")
        assert after == before + 1


class TestRecordAuthAttempt:
    @pytest.mark.parametrize("status", ["success", "expired", "invalid", "error"])
    def test_increments_for_each_status(self, status: str) -> None:
        from fastapi_keycloak_rbac.metrics import record_auth_attempt

        before = _get_sample_value("keycloak_rbac_auth_attempts_total", {"status": status})
        record_auth_attempt(status)
        after = _get_sample_value("keycloak_rbac_auth_attempts_total", {"status": status})
        assert after == before + 1


class TestRecordTokenValidation:
    @pytest.mark.parametrize("status", ["valid", "expired", "invalid", "error"])
    def test_increments_for_each_status(self, status: str) -> None:
        from fastapi_keycloak_rbac.metrics import record_token_validation

        before = _get_sample_value("keycloak_rbac_token_validations_total", {"status": status})
        record_token_validation(status)
        after = _get_sample_value("keycloak_rbac_token_validations_total", {"status": status})
        assert after == before + 1


class TestRecordKeycloakDuration:
    @pytest.mark.parametrize("operation", ["validate_token", "login"])
    def test_records_observation(self, operation: str) -> None:
        from fastapi_keycloak_rbac.metrics import record_keycloak_duration

        before = _get_sample_value(
            "keycloak_rbac_keycloak_operation_duration_seconds_count",
            {"operation": operation},
        )
        record_keycloak_duration(operation, 0.123)
        after = _get_sample_value(
            "keycloak_rbac_keycloak_operation_duration_seconds_count",
            {"operation": operation},
        )
        assert after == before + 1


class TestNoOpWhenPrometheusUnavailable:
    def test_record_cache_hit_no_op(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import fastapi_keycloak_rbac.metrics as m

        monkeypatch.setattr(m, "_prometheus_available", lambda: False)
        m.record_cache_hit()  # should not raise

    def test_record_auth_attempt_no_op(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import fastapi_keycloak_rbac.metrics as m

        monkeypatch.setattr(m, "_prometheus_available", lambda: False)
        m.record_auth_attempt("success")  # should not raise

    def test_record_keycloak_duration_no_op(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import fastapi_keycloak_rbac.metrics as m

        monkeypatch.setattr(m, "_prometheus_available", lambda: False)
        m.record_keycloak_duration("login", 0.5)  # should not raise
