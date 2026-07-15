"""Small metric utilities for reviewer-side experiments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BinaryMetrics:
    precision: float
    recall: float
    f1: float
    accuracy: float


def binary_metrics(labels: list[int], predictions: list[int]) -> BinaryMetrics:
    if len(labels) != len(predictions):
        raise ValueError("labels and predictions must have the same length")
    tp = sum(1 for y, p in zip(labels, predictions) if y == 1 and p == 1)
    fp = sum(1 for y, p in zip(labels, predictions) if y == 0 and p == 1)
    fn = sum(1 for y, p in zip(labels, predictions) if y == 1 and p == 0)
    tn = sum(1 for y, p in zip(labels, predictions) if y == 0 and p == 0)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(labels) if labels else 0.0
    return BinaryMetrics(precision=precision, recall=recall, f1=f1, accuracy=accuracy)


def auroc(labels: list[int], scores: list[float]) -> float:
    """Compute AUROC by pairwise ranking, avoiding external dependencies."""

    positives = [s for y, s in zip(labels, scores) if y == 1]
    negatives = [s for y, s in zip(labels, scores) if y == 0]
    if not positives or not negatives:
        raise ValueError("AUROC requires at least one positive and one negative")
    wins = 0.0
    total = len(positives) * len(negatives)
    for pos in positives:
        for neg in negatives:
            if pos > neg:
                wins += 1.0
            elif pos == neg:
                wins += 0.5
    return wins / total

