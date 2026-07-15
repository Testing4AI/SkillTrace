# SkillTrace Core

Compact reviewer-facing reference implementation for **SkillTrace: Multi-Trace
Provenance Auditing for LLM-Agent Skill Reuse**.

This artifact contains the core audit logic used to explain the paper method:
trace extraction, deterministic trace similarity, calibrated MaxFusion,
repository-level baselines, deterministic attack operators, and a small toy
example. It intentionally does **not** include benchmark datasets, wild-corpus
data, generated derivatives, paper result tables, or API keys.

## What Is Included

```text
src/skilltrace_core/
  parser.py        Skill package loader for SKILL.md plus support files
  traces.py        Expression, Implementation, and Operational trace extraction
  similarity.py    Jaccard, block/procedure/resource matching, SOG similarity
  audit.py         Calibrated MaxFusion audit procedure and CLI
  baselines.py     RepoClone-style whole-package and flat-text baselines
  attacks.py       Deterministic reuse/attack operators for smoke tests
  calibration.py   Q95 threshold calibration helpers
  evaluation.py    AUROC / precision / recall / F1 utilities

examples/minimal/
  anchor/          Tiny reference skill
  candidate/       Tiny derivative-like candidate

scripts/run_demo.py
tests/test_core.py
```

The release is designed to be readable by reviewers. It uses only the Python
standard library.

## Quick Start

```bash
cd reviewer_release/skilltrace-core
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

python -m skilltrace_core.audit \
  examples/minimal/anchor \
  examples/minimal/candidate \
  --pretty
```

Expected output is a JSON report with raw trace scores, calibrated ratios,
the final MaxFusion score, fired traces, and matched evidence snippets.

Run repository-level baselines:

```bash
python -m skilltrace_core.baselines \
  examples/minimal/anchor \
  examples/minimal/candidate \
  --pretty
```

Generate deterministic attack variants for local smoke tests:

```bash
python -m skilltrace_core.attacks \
  examples/minimal/anchor \
  /tmp/skilltrace_attacks \
  --pretty
```

The attack generator emits small packages for metadata rewrite, structural
reorganization, implementation lift with documentation rewrite,
documentation reuse with implementation rewrite, and deterministic dilution.

## Method Sketch

SkillTrace treats skill reuse as **trace preservation** rather than global
package similarity. It extracts three provenance traces from each skill:

- **Expression Trace**: authored prose, examples, trigger text, and rare textual
  identifiers.
- **Implementation Trace**: executable realization such as code blocks, support
  scripts, commands, API names, and configuration interfaces. This trace is
  marked not applicable when both sides do not contain enough implementation
  material.
- **Operational Trace**: a Skill Operational Graph (SOG) that abstracts how a
  skill is entered, what operational blocks it performs, how those blocks are
  ordered, and which tools/resources/artifacts they consume or produce.

At audit time, each trace is scored independently. Scores are normalized by
thresholds calibrated on same-function independent negatives, and MaxFusion
surfaces a pair when any calibrated trace exceeds the decision bound:

```text
max(score_expression / tau_expression,
    score_implementation / tau_implementation,
    score_operational / tau_operational) >= decision_bound
```

The default thresholds in this artifact are illustrative and should be replaced
with thresholds calibrated on the reviewer's own negative set.

## Operational Trace Note

The paper's full experimental pipeline caches an ingestion-time Operational
Trace. In this compact artifact, the default extractor is a deterministic
reference implementation so reviewers can run the code without LLM keys. The
audit-time scoring path is the important invariant: pairwise scoring is
deterministic and uses cached trace objects.

## Data Policy

This directory is safe to publish as a code artifact. It excludes:

- benchmark positives/negatives;
- wild-corpus skill packages;
- manual-review queues;
- generated attacks;
- result CSV/JSONL files;
- `.env` files and API keys.

If you add local data for reproduction, keep it outside this directory or under
paths ignored by `.gitignore`.

## Why This Is Not the Full Experiment Bundle

The complete paper experiments use private or large inputs: curated positives,
strict negatives, manual-review queues, wild-corpus candidate pairs, and
cached LLM-assisted Operational traces. Those are intentionally excluded from
the public code artifact. This repository is instead the reusable method
artifact: reviewers can inspect the implementation, run the toy example, add
their own skill pairs, and calibrate thresholds on their own negative set.
