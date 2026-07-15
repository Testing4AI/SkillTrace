from pathlib import Path

from skilltrace_core.audit import audit_pair
from skilltrace_core.attacks import generate_attacks
from skilltrace_core.baselines import compute_baselines


ROOT = Path(__file__).resolve().parents[1]


def test_minimal_demo_surfaces_candidate() -> None:
    report = audit_pair(ROOT / "examples/minimal/anchor", ROOT / "examples/minimal/candidate")
    assert report.surfaced
    assert report.maxfusion >= 1.0
    assert report.fired_traces


def test_baselines_run() -> None:
    scores = compute_baselines(ROOT / "examples/minimal/anchor", ROOT / "examples/minimal/candidate")
    assert scores.repo_jaccard > 0
    assert scores.flattext_jaccard > 0


def test_attack_generation(tmp_path: Path) -> None:
    generated = generate_attacks(ROOT / "examples/minimal/anchor", tmp_path)
    assert {item.family for item in generated} == {
        "metadata_rewrite",
        "structural_reorg",
        "implementation_lift_doc_rewrite",
        "doc_reuse_impl_rewrite",
        "dilution",
    }
    for item in generated:
        assert (Path(item.output) / "SKILL.md").exists()
