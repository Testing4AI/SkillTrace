"""Deterministic trace similarity functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .traces import OperationalTrace, TraceBundle


@dataclass(frozen=True)
class OperationalComponents:
    block: float
    activation: float
    procedure: float
    resource: float


@dataclass(frozen=True)
class TraceScores:
    expression: float
    implementation: float
    operational: float
    operational_components: OperationalComponents
    implementation_applicable: bool


def compute_trace_scores(reference: TraceBundle, candidate: TraceBundle) -> TraceScores:
    expression = jaccard(reference.expression.tokens, candidate.expression.tokens)
    implementation_applicable = (
        reference.implementation.applicable and candidate.implementation.applicable
    )
    implementation = (
        jaccard(reference.implementation.tokens, candidate.implementation.tokens)
        if implementation_applicable
        else 0.0
    )
    operational, components = operational_similarity(
        reference.operational, candidate.operational
    )
    return TraceScores(
        expression=expression,
        implementation=implementation,
        operational=operational,
        operational_components=components,
        implementation_applicable=implementation_applicable,
    )


def jaccard(a: set[str] | frozenset[str], b: set[str] | frozenset[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def operational_similarity(
    reference: OperationalTrace,
    candidate: OperationalTrace,
    weights: tuple[float, float, float, float] = (0.30, 0.10, 0.40, 0.20),
) -> tuple[float, OperationalComponents]:
    """Compare two Skill Operational Graphs.

    The four internal terms correspond to B, A, P, R in the SOG:
    operational blocks, activation signature, procedure edges, and
    resource-flow edges.
    """

    block_score = block_similarity(reference, candidate)
    activation_score = jaccard(reference.activation, candidate.activation)
    procedure_score = procedure_similarity(reference, candidate)
    resource_score = edge_jaccard(reference.resource_edges, candidate.resource_edges)
    score = (
        weights[0] * block_score
        + weights[1] * activation_score
        + weights[2] * procedure_score
        + weights[3] * resource_score
    )
    return score, OperationalComponents(
        block=block_score,
        activation=activation_score,
        procedure=procedure_score,
        resource=resource_score,
    )


def block_similarity(reference: OperationalTrace, candidate: OperationalTrace) -> float:
    labels_r = [b.label for b in reference.blocks]
    labels_c = [b.label for b in candidate.blocks]
    match = multiset_match_score(labels_r, labels_c)
    order = lcs_score(labels_r, labels_c)
    return 0.80 * match + 0.20 * order


def procedure_similarity(reference: OperationalTrace, candidate: OperationalTrace) -> float:
    edge = edge_jaccard(reference.procedure_edges, candidate.procedure_edges)
    labels_r = [b.label for b in reference.blocks]
    labels_c = [b.label for b in candidate.blocks]
    order = lcs_score(labels_r, labels_c)
    return 0.70 * edge + 0.30 * order


def edge_jaccard(
    a: set[tuple[str, str, str]] | frozenset[tuple[str, str, str]],
    b: set[tuple[str, str, str]] | frozenset[tuple[str, str, str]],
) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def multiset_match_score(a: Sequence[str], b: Sequence[str]) -> float:
    if not a or not b:
        return 0.0
    counts: dict[str, int] = {}
    for label in b:
        counts[label] = counts.get(label, 0) + 1
    matches = 0
    for label in a:
        if counts.get(label, 0) > 0:
            matches += 1
            counts[label] -= 1
    return matches / max(len(a), len(b))


def lcs_score(a: Sequence[str], b: Sequence[str]) -> float:
    if not a or not b:
        return 0.0
    prev = [0] * (len(b) + 1)
    for item_a in a:
        curr = [0] * (len(b) + 1)
        for j, item_b in enumerate(b, start=1):
            if item_a == item_b:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr
    return prev[-1] / max(len(a), len(b))

