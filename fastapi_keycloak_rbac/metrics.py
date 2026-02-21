"""
Prometheus metrics for fastapi-keycloak-rbac.

Provides counters and histograms for monitoring Keycloak authentication
operations. Requires the ``metrics`` optional extra:

    pip install fastapi-keycloak-rbac[metrics]

Metrics are only recorded when ``prometheus-client`` is installed. If it is
not installed, all ``record_*`` functions become no-ops so the rest of the
package works unchanged.

Metric names
------------
- ``keycloak_rbac_token_cache_hits_total``
- ``keycloak_rbac_token_cache_misses_total``
- ``keycloak_rbac_auth_attempts_total{status}``       — success|expired|invalid|error
- ``keycloak_rbac_token_validations_total{status}``   — valid|expired|invalid|error
- ``keycloak_rbac_keycloak_operation_duration_seconds{operation}`` — validate_token|login

Example::

    from fastapi_keycloak_rbac.metrics import record_cache_hit, record_keycloak_duration
    import time

    t0 = time.monotonic()
    claims = await manager.decode_token(token)
    record_keycloak_duration("validate_token", time.monotonic() - t0)
    record_cache_miss()
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_DURATION_BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)

# Registry of already-created metric objects, keyed by name.
# This prevents duplicate-registration errors when using --reload.
_registry: dict[str, Any] = {}


def _get_or_create_counter(name: str, doc: str, labels: list[str] | None = None) -> Any:
    if name not in _registry:
        from prometheus_client import Counter

        _registry[name] = Counter(name, doc, labels or [])
    return _registry[name]


def _get_or_create_histogram(
    name: str,
    doc: str,
    labels: list[str] | None = None,
    buckets: tuple[float, ...] = _DURATION_BUCKETS,
) -> Any:
    if name not in _registry:
        from prometheus_client import Histogram

        _registry[name] = Histogram(name, doc, labels or [], buckets=buckets)
    return _registry[name]


def _prometheus_available() -> bool:
    try:
        import prometheus_client  # noqa: F401

        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Public record_* functions
# ---------------------------------------------------------------------------


def record_cache_hit() -> None:
    """Increment the token cache hit counter."""
    if not _prometheus_available():
        return
    _get_or_create_counter(
        "keycloak_rbac_token_cache_hits_total",
        "Total number of token cache hits.",
    ).inc()


def record_cache_miss() -> None:
    """Increment the token cache miss counter."""
    if not _prometheus_available():
        return
    _get_or_create_counter(
        "keycloak_rbac_token_cache_misses_total",
        "Total number of token cache misses.",
    ).inc()


def record_auth_attempt(status: str) -> None:
    """
    Increment the authentication attempt counter.

    Args:
        status: One of ``success``, ``expired``, ``invalid``, ``error``.
    """
    if not _prometheus_available():
        return
    _get_or_create_counter(
        "keycloak_rbac_auth_attempts_total",
        "Total number of authentication attempts.",
        ["status"],
    ).labels(status=status).inc()


def record_token_validation(status: str) -> None:
    """
    Increment the token validation counter.

    Args:
        status: One of ``valid``, ``expired``, ``invalid``, ``error``.
    """
    if not _prometheus_available():
        return
    _get_or_create_counter(
        "keycloak_rbac_token_validations_total",
        "Total number of token validation results.",
        ["status"],
    ).labels(status=status).inc()


def record_keycloak_duration(operation: str, seconds: float) -> None:
    """
    Observe a Keycloak operation duration.

    Args:
        operation: One of ``validate_token``, ``login``.
        seconds: Elapsed time in seconds.
    """
    if not _prometheus_available():
        return
    _get_or_create_histogram(
        "keycloak_rbac_keycloak_operation_duration_seconds",
        "Duration of Keycloak operations in seconds.",
        ["operation"],
    ).labels(operation=operation).observe(seconds)
