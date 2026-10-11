# Anonymous artifact scope

## Included

* Executable three-trace registration and audit implementation.
* SOG schema checks, closed showcase vocabulary and ingestion prompt.
* Source/configuration keyed caches and deterministic local scoring.
* Independent negative calibration and MaxFusion.
* Whole-package Jaccard and optional ssdeep baseline runner.
* Two authored seeds, four variants, source-supported annotations and cached traces.
* Paper-reported aggregate comparisons and a paper-to-code method map.
* Complete non-sentinel wild-corpus metadata inventory and saved run summary.
* Two selected observed pairs with short excerpts, saved scores and file hashes.
* Corresponding local SOG annotations and a side-by-side diagram for the differently named pair.
* Portable own-seed variant generation, including optional LLM transformations.

## Excluded

The full benchmark, N0/N1/N2 pairs, anchor inventory, attack-generation batches,
full wild-corpus packages, human-review records, and full per-pair prediction files
are withheld. There are no corpus-fetch or benchmark-download scripts in the package.
This release cannot regenerate the aggregate benchmark metrics without those inputs.

## Relationship to the paper

The executable flow follows registration-time SOG extraction and cached audit-time
comparison. It uses the paper's five-field blocks, three SOG views, outer weights,
trace-specific calibration and MaxFusion rule. There is no default keyword-based
Operational extractor. Source instructions are read as data, never executed.

Public code makes its tokenization, exact-label block matching, tie convention and
inner mixtures explicit in [METHOD.md](METHOD.md). Public annotations/vocabulary
are demonstration fixtures, rather than the original experimental caches. The
paper's full evaluation is represented by the reported aggregate tables.

The LLM client is optional. Local verification uses mocked responses to check the
client contract; no live paid provider call is needed to run this artifact.
The public generator is a portable transformation subset, not the original private
batch pipeline. The metadata inventory and observed cases are documented separately
in [WILD_AUDIT.md](WILD_AUDIT.md).

## Clean packaging

```bash
python3 scripts/check_release.py
python3 scripts/package_release.py --output ../skilltrace-anonymous.zip
```

The packaging command uses an allowlist. It excludes generated `outputs/`, local
environments, credentials, caches created by Python, benchmark directories and Git
history. The source-trace fixtures under `examples/cache/` are explicitly included.
Checksums inside the archive cover each distributed file.

Upload the extracted archive contents as the anonymous repository root, so the
README and its relative links resolve. The package creates no remote repository
and does not modify an existing repository's history.

## Attribution and review status

Authorship and affiliations are withheld for anonymous review. The new gallery
packages are authored demonstrations. The separate wild-case records contain only
short third-party excerpts, identifiers and evidence hashes, not complete packages.
The overview figure comes from the accompanying anonymous manuscript.
No software license has been assigned by this packaging step; a public repository
should not be interpreted as granting an unstated license.
