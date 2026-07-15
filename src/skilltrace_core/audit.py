"""SkillTrace audit procedure and CLI."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .parser import load_skill_package
from .similarity import TraceScores, compute_trace_scores
from .traces import TraceBundle, extract_traces


@dataclass(frozen=True)
class Thresholds:
    """Per-trace thresholds calibrated from same-function independent negatives."""

    expression: float = 0.18
    implementation: float = 0.14
    operational: float = 0.40
    decision_bound: float = 1.0


@dataclass(frozen=True)
class AuditReport:
    reference: str
    candidate: str
    scores: dict[str, Any]
    calibrated: dict[str, float]
    maxfusion: float
    decision_bound: float
    surfaced: bool
    fired_traces: tuple[str, ...]
    evidence: dict[str, Any]


def audit_pair(
    reference_root: str | Path,
    candidate_root: str | Path,
    thresholds: Thresholds | None = None,
) -> AuditReport:
    """Audit a candidate skill against a reference skill."""

    thresholds = thresholds or Thresholds()
    ref_pkg = load_skill_package(reference_root)
    cand_pkg = load_skill_package(candidate_root)
    ref_traces = extract_traces(ref_pkg)
    cand_traces = extract_traces(cand_pkg)
    scores = compute_trace_scores(ref_traces, cand_traces)
    calibrated = _calibrated(scores, thresholds)
    maxfusion = max(calibrated.values())
    fired = tuple(k for k, value in calibrated.items() if value >= thresholds.decision_bound)
    return AuditReport(
        reference=str(ref_pkg.root),
        candidate=str(cand_pkg.root),
        scores=_score_dict(scores),
        calibrated=calibrated,
        maxfusion=maxfusion,
        decision_bound=thresholds.decision_bound,
        surfaced=maxfusion >= thresholds.decision_bound,
        fired_traces=fired,
        evidence=_collect_evidence(ref_traces, cand_traces, fired),
    )


def _score_dict(scores: TraceScores) -> dict[str, Any]:
    return {
        "expression": scores.expression,
        "implementation": scores.implementation,
        "implementation_applicable": scores.implementation_applicable,
        "operational": scores.operational,
        "operational_components": asdict(scores.operational_components),
    }


def _calibrated(scores: TraceScores, thresholds: Thresholds) -> dict[str, float]:
    return {
        "expression": _safe_ratio(scores.expression, thresholds.expression),
        "implementation": (
            _safe_ratio(scores.implementation, thresholds.implementation)
            if scores.implementation_applicable
            else 0.0
        ),
        "operational": _safe_ratio(scores.operational, thresholds.operational),
    }


def _safe_ratio(score: float, threshold: float) -> float:
    if threshold <= 0:
        return 0.0
    return score / threshold


def _collect_evidence(
    reference: TraceBundle,
    candidate: TraceBundle,
    fired_traces: tuple[str, ...],
) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    if "expression" in fired_traces:
        evidence["expression_tokens"] = sorted(
            reference.expression.tokens & candidate.expression.tokens
        )[:30]
    if "implementation" in fired_traces:
        evidence["implementation_tokens"] = sorted(
            reference.implementation.tokens & candidate.implementation.tokens
        )[:30]
    if "operational" in fired_traces:
        ref_labels = {b.label for b in reference.operational.blocks}
        cand_labels = {b.label for b in candidate.operational.blocks}
        evidence["operational_blocks"] = sorted(ref_labels & cand_labels)[:20]
        evidence["procedure_edges"] = sorted(
            reference.operational.procedure_edges & candidate.operational.procedure_edges
        )[:20]
        evidence["resource_edges"] = sorted(
            reference.operational.resource_edges & candidate.operational.resource_edges
        )[:20]
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit a candidate skill with SkillTrace core.")
    parser.add_argument("reference", help="Path to reference skill package")
    parser.add_argument("candidate", help="Path to candidate skill package")
    parser.add_argument("--tau-expression", type=float, default=Thresholds.expression)
    parser.add_argument("--tau-implementation", type=float, default=Thresholds.implementation)
    parser.add_argument("--tau-operational", type=float, default=Thresholds.operational)
    parser.add_argument("--decision-bound", type=float, default=Thresholds.decision_bound)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args(argv)

    report = audit_pair(
        args.reference,
        args.candidate,
        Thresholds(
            expression=args.tau_expression,
            implementation=args.tau_implementation,
            operational=args.tau_operational,
            decision_bound=args.decision_bound,
        ),
    )
    print(json.dumps(asdict(report), indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

