# Build a dataset from your own seeds

The public generator creates **source-derived candidate pairs** from a text skill
package containing `SKILL.md`. It is a portable subset of transformation families,
not the original batch runner or a reconstruction of the withheld benchmark.
No benchmark download, original seed or private service is required.

## Offline transformations

```bash
python3 scripts/generate_variants.py \
  --seed examples/form/seed --output outputs/my-form-dataset \
  --families metadata_rewrite dilution --rng-seed 17
```

Replace the seed path with your own skill directory. Metadata rewriting changes
the frontmatter name; dilution appends ancillary prose. Both preserve existing
code and support-file text. The same input and RNG seed produce the same offline
variants. These simple transformations do not guarantee that a detector is evaded.

## Optional LLM transformations

Configure `SKILLTRACE_LLM_URL` with your provider's HTTPS chat-completions endpoint
and `SKILLTRACE_API_KEY` through your environment. Do not commit credentials.
Only run this on source material you are authorized to send to that provider.

```bash
# Replace MODEL_ID with a model supported by your provider.
python3 scripts/generate_variants.py \
  --seed examples/watchlist/seed --output outputs/watchlist-rewrite \
  --families llm_rewrite --model MODEL_ID

python3 scripts/generate_variants.py \
  --seed examples/watchlist/seed --output outputs/watchlist-translation \
  --families natural_language_translation --language Chinese --model MODEL_ID

python3 scripts/generate_variants.py \
  --seed examples/form/seed --output outputs/form-port \
  --families code_language_port --language JavaScript --model MODEL_ID
```

| Family | Intended change | Review focus |
| :--- | :--- | :--- |
| `metadata_rewrite` | Rename the skill | Interface references still consistent |
| `dilution` | Add ancillary prose | No conflicting operational instructions |
| `llm_rewrite` | Rephrase and reorganize prose | Branches, dependencies and task intent retained |
| `natural_language_translation` | Change instruction language | Meaning and identifiers retained |
| `code_language_port` | Rewrite code in another language | APIs, semantics, dependencies and build setup |

The port mode preserves paths to keep a reviewable file mapping. File extensions,
build configuration and environment may need manual adjustment; its output is not
promised to execute. An unchanged or failed transformation must be rejected during
review. LLM calls incur provider costs; temperature zero does not guarantee identical
responses. The artifact tests mock this interface rather than claiming live-provider
or semantic validation.

## Outputs and experimental use

Each new output directory contains `seed/`, one directory per transformation, and
`manifest.json`. The manifest records package digests, pair IDs, family, generation
configuration, requested/returned model where applicable, and **pending** utility
and attack-success review fields. It contains no API key or absolute source path.
Existing outputs are never overwritten. Skill contents are never executed.

The generator accepts supported text files only and rejects visible unsupported
assets instead of silently omitting them. Use one output directory per seed. Inspect
generated text before executing any code; generated instructions are untrusted.

To construct an evaluation dataset:

1. Generate variants from seeds you may use and redistribute.
2. Review whether each transformation succeeded and preserved the required utility;
   source-derived lineage alone is not a sufficient positive label.
3. Register each accepted package independently to extract its own SOG. Do not copy
   seed annotations into variants or assume a shared Operational score.
4. Supply independent negative pairs and a source-disjoint calibration set. The
   generator does not label unrelated seeds as negatives automatically.
5. Freeze calibration thresholds, then audit and report the held-out results.

No newly generated pair is included in the paper's reported benchmark results.
