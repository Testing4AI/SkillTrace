"""Threshold calibration helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CalibratedThresholds:
    expression: float
    implementation: float
    operational: float


def quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("Cannot compute a quantile of an empty list")
    if not 0 <= q <= 1:
        raise ValueError("q must be in [0, 1]")
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))
    return ordered[idx]


def calibrate_q95(
    expression_scores: list[float],
    implementation_scores: list[float],
    operational_scores: list[float],
) -> CalibratedThresholds:
    """Calibrate per-trace thresholds at the 95th negative percentile."""

    return CalibratedThresholds(
        expression=quantile(expression_scores, 0.95),
        implementation=quantile(implementation_scores, 0.95),
        operational=quantile(operational_scores, 0.95),
    )

