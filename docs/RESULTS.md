# Paper-reported results

The README comparison table is transcribed from Table 4, “Global detection
effectiveness,” in the accompanying paper. No table entry is recomputed from the
demonstration fixtures. No benchmark per-pair evaluation data is included. Two
selected wild-audit score records are available in [WILD_AUDIT.md](WILD_AUDIT.md).

## Evaluation composition

| Set | Purpose | Pairs | Used to fit thresholds? |
| :--- | :--- | ---: | :--- |
| N0 | Independent same-function calibration negatives | 100 | Yes |
| Positive evaluation | Repackaging, porting/rewriting, partial reuse | 820 | No |
| N1 | Same-function strict evaluation negatives | 551 | No |
| N2 | Clean-room synthetic evaluation negatives | 200 | No |

N0 is outside the 751 evaluation-negative total. N2 is generated using multiple
LLMs from task metadata without the original skill body. The positive evaluation
draws on 100 public skill anchors and includes observed ecosystem reuse and
controlled transformations.

## What the baselines compare

* **RepoClone-Jaccard:** whole-package token overlap.
* **RepoClone-ssdeep:** fuzzy hashing of the package's flattened contents.
* **RepoClone-Max:** maximum normalized baseline score, restricted to components
  with positive calibration thresholds. A zero ssdeep threshold uses strict positive
  detection for its individual rate and is never a ratio denominator.
* **Single-trace ablations:** E, I, or O alone. I uses its applicable subset.
* **Linear fusion:** mean of applicable normalized E/I/O scores.
* **SkillTrace-MaxFusion:** maximum of applicable normalized E/I/O scores.

The reported precision/recall trade-off remains visible: Linear fusion has the
highest precision (0.973), while MaxFusion has the highest recall (0.883) and F1
(0.898). The method aims to preserve localized evidence when other traces weaken.

## Rewrite results and calibration context

Table 3 reports these P3 full-LLM-rewrite detection rates:

| Method | Detection rate |
| :--- | ---: |
| RepoClone-Jaccard | 0.32 |
| RepoClone-ssdeep | 0.02 |
| Expression | 0.31 |
| Implementation (applicable subset) | 0.24 |
| Operational | 0.73 |
| MaxFusion | 0.78 |

The same table reports MaxFusion FPRs of 0.12 on N0, 0.09 on N1 and 0.12 on N2.
The 5% nominal target applies separately to each trace's calibration rule and
does not imply a 5% final fused FPR. AUROC is a ranking metric; thresholded precision,
recall, F1 and FPR describe the stated operating point.

The public examples expose mechanisms, source fields and matching behavior. They
do not estimate detection accuracy, extraction reliability, or cross-language
generalization; the research claims refer to the paper's evaluation.
