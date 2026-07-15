"""Repository-level and flat-text baselines.

These baselines are intentionally small, deterministic implementations for
artifact review. They mirror the measurement style used in the paper without
shipping any benchmark data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .parser import SkillPackage, load_skill_package
from .traces import _strip_code_fences, _tokens


@dataclass(frozen=True)
class BaselineScores:
    repo_jaccard: float
    flattext_jaccard: float
    ssdeep: float | None
    ssdeep_available: bool


def compute_baselines(reference_root: str | Path, candidate_root: str | Path) -> BaselineScores:
    ref = load_skill_package(reference_root)
    cand = load_skill_package(candidate_root)
    return BaselineScores(
        repo_jaccard=repo_jaccard(ref, cand),
        flattext_jaccard=flattext_jaccard(ref, cand),
        ssdeep=ssdeep_similarity(ref, cand),
        ssdeep_available=_ssdeep_available(),
    )


def repo_jaccard(reference: SkillPackage, candidate: SkillPackage) -> float:
    """Whole-package token Jaccard over all loaded text files."""

    return _jaccard(
        set(_tokens(reference.all_text(), keep_stopwords=True)),
        set(_tokens(candidate.all_text(), keep_stopwords=True)),
    )


def flattext_jaccard(reference: SkillPackage, candidate: SkillPackage) -> float:
    """Jaccard over natural-language skill text with fenced code removed."""

    ref_text = _strip_code_fences(reference.skill_md)
    cand_text = _strip_code_fences(candidate.skill_md)
    return _jaccard(set(_tokens(ref_text)), set(_tokens(cand_text)))


def ssdeep_similarity(reference: SkillPackage, candidate: SkillPackage) -> float | None:
    """Return ssdeep similarity in [0, 1] when the optional package is installed.

    The artifact does not depend on ssdeep because installing fuzzy-hash native
    extensions can be fragile in reviewer environments.
    """

    try:
        import ssdeep  # type: ignore
    except Exception:
        return None
    h1 = ssdeep.hash(reference.all_text())
    h2 = ssdeep.hash(candidate.all_text())
    return ssdeep.compare(h1, h2) / 100.0


def content_hash(package: SkillPackage) -> str:
    return hashlib.sha256(package.all_text().encode("utf-8")).hexdigest()


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _ssdeep_available() -> bool:
    try:
        import ssdeep  # noqa: F401
    except Exception:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run repository-level baseline scores.")
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    scores = compute_baselines(args.reference, args.candidate)
    payload: dict[str, Any] = asdict(scores)
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

