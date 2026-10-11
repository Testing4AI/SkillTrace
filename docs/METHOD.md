# Method and implementation

The public implementation follows the paper's three-trace architecture and
registration/audit split. The table below connects the method to executable code.

| Paper component | Public implementation |
| :--- | :--- |
| Expression Trace (§3.3.1) | `core.extract_ei`: document prose, stopword/scaffold filtering, token Jaccard |
| Implementation Trace (§3.3.2) | Fenced code in documents, inline executable fragments, command lines, support code/configuration |
| SOG (§3.4) | Five-field blocks, Activation/Procedure/Resource-Flow relations, shared IDs, closed vocabulary |
| Ingestion-time extraction | `ingestion.extract_sog`: one package per model request, schema and source-quote validation |
| Versioned trace cache | Content digest, vocabulary and extractor configuration digest, cache key and integrity digest |
| Trace similarity (§3.5.1–2) | `core.compare`, `core.compare_sog` |
| Independent calibration (§3.5.3) | `core.calibrate`: per-trace negative quantiles; rejects overlapping pair IDs |
| MaxFusion (§3.5.3) | `core.audit`: strongest applicable score/threshold ratio, decision bound 1 |
| Evidence reporting (§3.6) | Shared E/I tokens, matched SOG labels/relations, source-file quote pointers |

## SOG contract

Each block has `action`, `object_role`, `tool_role`, `inputs`, and `outputs`.
Its ID only links the three views; renaming IDs does not affect scores. Every block
and relation has a package-relative source file and an exact supporting quote.
Quote occurrence is mechanically checked. Whether that quote supports the extracted
meaning remains a semantic review question.

Activation records an intent, required context and initial block. Procedure records
directed relations and their conditions. Resource-Flow records `consumes`, `produces`
or `uses_tool`, written from a block to an artifact/tool role. Consuming an artifact
and producing it are distinct relations even when their endpoint roles are identical.

Inspect the [watchlist annotation](../examples/annotations/watchlist_seed.json).
The SOG describes published operational instructions; it is not an executed trace.

## Exact public scoring conventions

E and I use token Jaccard. The language-agnostic tokenizer retains Unicode word
tokens, path-like identifiers and command options. The implementation threshold is
200 extracted code/command characters on each side. An inapplicable I score is
`null`, with no I term in fusion.

For O, the public implementation instantiates maximum one-to-one block matching
as equality of normalized five-field labels. Multiset intersection computes its
maximum match count exactly, including duplicate blocks; the count is normalized
by the larger block set. Local IDs and quotes are excluded. Inputs and outputs
are canonicalized as role sets.

```text
BlockSim = 0.80 × normalized maximum label match + 0.20 × normalized LCS
ActSim   = Jaccard of normalized (intent, context, entry-block) signatures
ProcSim  = 0.70 × typed procedure-edge Jaccard + 0.30 × normalized LCS
ResSim   = Jaccard of directed typed block–resource relations
O        = 0.30 × BlockSim + 0.10 × ActSim + 0.40 × ProcSim + 0.20 × ResSim
```

LCS uses the supplied normalized block order. Procedure matching includes condition
roles and edge direction. Empty feature-set overlap is zero, rather than perfect
similarity. Registration rejects empty SOGs. All scoring is symmetric and deterministic.
These conventions make the released implementation explicit; exact reproduction of
the historical results additionally needs the withheld experimental inputs, frozen
extraction vocabulary, caches, and configuration.

## LLM extraction for new packages

Choose and freeze a role vocabulary before extracting the skills to be compared.
`config/showcase_vocabulary.json` covers only the two demonstration domains and is
not presented as the original benchmark vocabulary. The full extraction prompt is
in `src/skilltrace/ingestion.py`.

The optional client accepts an OpenAI-compatible chat-completions endpoint. Set
`SKILLTRACE_LLM_URL` to its HTTPS URL and `SKILLTRACE_API_KEY` in your local environment.
Then run:

```bash
PYTHONPATH=src python3 -m skilltrace register path/to/skill \
  --model YOUR_MODEL_ID \
  --vocabulary path/to/frozen_vocabulary.json \
  --output outputs/new-skill.json
```

The request sees one skill only. It does not see another skill, a target score or
a reuse label. The public client uses temperature 0 and an 8,192-token output cap;
it records requested/returned model IDs and a prompt digest. Invalid vocabulary,
unknown source quotes and dangling graph references are rejected. Large inputs
fail explicitly rather than being silently truncated. Review imported/model-generated
annotations before using them for an audit.

Repeated `audit` calls consume only caches. They do not read credentials or import
an LLM backend. A cache is identified by source content and extraction configuration;
changed skill content requires registration again. Cache integrity detects accidental
modification, not malicious tampering by someone able to recompute the digest.

## Independent calibration

Supply scores from same-function, independently implemented negative pairs:

```json
[
  {"pair_id": "cal-001", "label": 0,
   "scores": {"expression": 0.12, "implementation": null, "operational": 0.28}}
]
```

This is a format illustration, not a sufficient calibration sample. Provide enough
applicable negatives for every trace, including Implementation. Store the evaluation
pair IDs in a separate JSON array, then run:

```bash
PYTHONPATH=src python3 -m skilltrace calibrate private/calibration_scores.json \
  --evaluation-ids private/evaluation_pair_ids.json \
  --alpha 0.05 --output outputs/thresholds.json
```

The public routine uses the nearest-rank empirical `(1−alpha)` quantile. It rejects
positive calibration labels, duplicate IDs, overlapping calibration/evaluation IDs,
nonfinite scores, and zero ratio denominators. ID checks supplement dataset curation;
they do not establish source/provenance disjointness by themselves. All evaluation
scores use fixed thresholds. Nominal 5% per-trace calibration does not guarantee
5% fused FPR; report actual held-out FPR after fusion.

The five-field representation and three SOG views are unchanged when extending
the extractor or adding a supplementary Implementation matcher, such as AST features.
