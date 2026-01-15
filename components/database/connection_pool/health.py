"""
Database Health Check Module.

LEGO Component: database/connection-pool
Purpose: Health check logic for PostgreSQL connections

Usage:
    from health import DatabaseHealthChecker, HealthStatus

    checker = DatabaseHealthChecker(pool)
    status = await checker.check()

    if status.is_healthy:
        print("Database is healthy")
    else:
        print(f"Database unhealthy: {status.message}")
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class HealthState(Enum):
    """Health check states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthStatus:
    """Health check result."""
    state: HealthState
    message: str
    latency_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: dict = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        """Check if status indicates healthy state."""
        return self.state == HealthState.HEALTHY

    @property
    def is_degraded(self) -> bool:
        """Check if status indicates degraded state."""
        return self.state == HealthState.DEGRADED

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "state": self.state.value,
            "message": self.message,
            "latency_ms": round(self.latency_ms, 2),
            "timestamp": self.timestamp.isoformat(),
            "is_healthy": self.is_healthy,
            "details": self.details,
        }


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""
    timeout_seconds: float = 5.0
    latency_warning_ms: float = 100.0
    latency_critical_ms: float = 500.0
    min_pool_available: int = 1
    check_interval_seconds: float = 30.0


class DatabaseHealthChecker:
    """
    Health checker for database connections.

    Features:
    - Connection health verification
    - Latency measurement
    - Pool status monitoring
    - Degraded state detection
    - Historical health tracking
    """

    def __init__(
        self,
        pool: Any,  # ConnectionPool type
        config: Optional[HealthCheckConfig] = None,
    ):
        self.pool = pool
        self.config = config or HealthCheckConfig()
        self._history: List[HealthStatus] = []
        self._max_history = 100
        self._consecutive_failures = 0

    async def check(self) -> HealthStatus:
        """
        Perform a comprehensive health check.

        Returns:
            HealthStatus with state, message, and latency
        """
        start_time = time.perf_counter()

        try:
            # Check if pool is initialized
            if not self.pool._initialized:
                return self._create_status(
                    HealthState.UNHEALTHY,
                    "Connection pool not initialized",
                    0.0,
                )

            # Execute health check query with timeout
            try:
                async with asyncio.timeout(self.config.timeout_seconds):
                    async with self.pool.session() as session:
                        result = await session.execute(
                            text("SELECT 1 as health_check")
                        )
                        row = result.scalar()

                        if row != 1:
                            raise ValueError("Unexpected health check result")

            except asyncio.TimeoutError:
                latency = (time.perf_counter() - start_time) * 1000
                self._consecutive_failures += 1
                return self._create_status(
                    HealthState.UNHEALTHY,
                    f"Health check timed out after {self.config.timeout_seconds}s",
                    latency,
                )

            latency_ms = (time.perf_counter() - start_time) * 1000

            # Check pool statistics
            pool_stats = self.pool.get_stats()

            # Determine health state based on latency and pool status
            state, message = self._evaluate_health(latency_ms, pool_stats)

            # Reset consecutive failures on success
            if state == HealthState.HEALTHY:
                self._consecutive_failures = 0
            elif state == HealthState.DEGRADED:
                self._consecutive_failures = max(0, self._consecutive_failures - 1)

            return self._create_status(state, message, latency_ms, pool_stats)

        except SQLAlchemyError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._consecutive_failures += 1
            logger.error(f"Database health check failed: {e}")
            return self._create_status(
                HealthState.UNHEALTHY,
                f"Database error: {str(e)[:100]}",
                latency_ms,
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._consecutive_failures += 1
            logger.exception(f"Unexpected health check error: {e}")
            return self._create_status(
                HealthState.UNKNOWN,
                f"Unexpected error: {str(e)[:100]}",
                latency_ms,
            )

    def _evaluate_health(
        self,
        latency_ms: float,
        pool_stats: dict,
    ) -> tuple[HealthState, str]:
        """Evaluate health state based on metrics."""
        issues: List[str] = []

        # Check latency
        if latency_ms >= self.config.latency_critical_ms:
            issues.append(f"High latency: {latency_ms:.0f}ms")
        elif latency_ms >= self.config.latency_warning_ms:
            issues.append(f"Elevated latency: {latency_ms:.0f}ms")

        # Check pool availability
        checked_in = pool_stats.get("checked_in", 0)
        if checked_in < self.config.min_pool_available:
            issues.append(f"Low pool availability: {checked_in} connections")

        # Check for high overflow
        overflow = pool_stats.get("overflow", 0)
        pool_size = pool_stats.get("pool_size", 1)
        if overflow > pool_size:
            issues.append(f"High overflow: {overflow} connections")

        # Check error rate
        error_count = pool_stats.get("error_count", 0)
        query_count = pool_stats.get("query_count", 1)
        if query_count > 0 and error_count / query_count > 0.1:
            issues.append(f"High error rate: {error_count}/{query_count}")

        # Determine state
        if not issues:
            return HealthState.HEALTHY, "Database connection healthy"

        if len(issues) == 1 and "Elevated latency" in issues[0]:
            return HealthState.DEGRADED, issues[0]

        if self._consecutive_failures >= 3:
            return HealthState.UNHEALTHY, "; ".join(issues)

        return HealthState.DEGRADED, "; ".join(issues)

    def _create_status(
        self,
        state: HealthState,
        message: str,
        latency_ms: float,
        pool_stats: Optional[dict] = None,
    ) -> HealthStatus:
        """Create and track health status."""
        status = HealthStatus(
            state=state,
            message=message,
            latency_ms=latency_ms,
            details={
                "pool_stats": pool_stats or {},
                "consecutive_failures": self._consecutive_failures,
            },
        )

        # Track history
        self._history.append(status)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return status

    def get_history(self, limit: int = 10) -> List[dict]:
        """Get recent health check history."""
        return [s.to_dict() for s in self._history[-limit:]]

    def get_summary(self) -> dict:
        """Get health check summary statistics."""
        if not self._history:
            return {"total_checks": 0}

        recent = self._history[-100:]
        healthy_count = sum(1 for s in recent if s.is_healthy)
        avg_latency = sum(s.latency_ms for s in recent) / len(recent)

        return {
            "total_checks": len(self._history),
            "recent_healthy_rate": healthy_count / len(recent),
            "average_latency_ms": round(avg_latency, 2),
            "consecutive_failures": self._consecutive_failures,
            "last_check": self._history[-1].to_dict() if self._history else None,
        }


class HealthCheckEndpoint:
    """
    FastAPI-compatible health check endpoint helper.

    Usage:
        from fastapi import FastAPI
        from health import HealthCheckEndpoint

        app = FastAPI()
        health_endpoint = HealthCheckEndpoint(pool)

        @app.get("/health")
        async def health():
            return await health_endpoint.check()

        @app.get("/health/detailed")
        async def health_detailed():
            return await health_endpoint.detailed_check()
    """

    def __init__(self, pool: Any, config: Optional[HealthCheckConfig] = None):
        self.checker = DatabaseHealthChecker(pool, config)

    async def check(self) -> dict:
        """Simple health check returning status and latency."""
        status = await self.checker.check()
        return {
            "status": status.state.value,
            "database": "ok" if status.is_healthy else "error",
        }

    async def detailed_check(self) -> dict:
        """Detailed health check with full metrics."""
        status = await self.checker.check()
        return {
            "status": status.state.value,
            "database": status.to_dict(),
            "summary": self.checker.get_summary(),
        }

    async def readiness_check(self) -> tuple[dict, int]:
        """
        Kubernetes-style readiness check.

        Returns:
            Tuple of (response_body, http_status_code)
        """
        status = await self.checker.check()

        if status.is_healthy:
            return {"ready": True}, 200
        if status.is_degraded:
            return {"ready": True, "degraded": True}, 200
        return {"ready": False, "message": status.message}, 503

    async def liveness_check(self) -> tuple[dict, int]:
        """
        Kubernetes-style liveness check.

        Returns:
            Tuple of (response_body, http_status_code)
        """
        # Liveness is less strict - only fail on complete inability to connect
        status = await self.checker.check()

        if status.state != HealthState.UNHEALTHY:
            return {"alive": True}, 200
        else:
            return {"alive": False, "message": status.message}, 503
