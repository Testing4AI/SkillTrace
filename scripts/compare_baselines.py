"""Whole-package baselines, with optional ssdeep and explicit missingness."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from skilltrace.core import jaccard, load_package, tokens


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("--thresholds", default=str(ROOT / "config/paper_thresholds.json"))
    args = parser.parse_args()
    left = "\n\n".join(load_package(args.reference).values())
    right = "\n\n".join(load_package(args.candidate).values())
    scores = {"repo_jaccard": jaccard(tokens(left), tokens(right)), "ssdeep": None}
    try:
        import ssdeep
    except ImportError:
        pass
    else:
        scores["ssdeep"] = ssdeep.compare(ssdeep.hash(left), ssdeep.hash(right)) / 100
    config = json.loads(Path(args.thresholds).read_text())
    thresholds = config["baseline_thresholds"]
    positive_ratios = {k: v / thresholds[k] for k, v in scores.items()
                       if v is not None and thresholds[k] > 0}
    fired = {k: None if v is None else (v > 0 if thresholds[k] == 0 else v >= thresholds[k])
             for k, v in scores.items()}
    print(json.dumps({"scores": scores, "ssdeep_available": scores["ssdeep"] is not None,
                      "fired": fired, "repoclone_max": max(positive_ratios.values()),
                      "positive_threshold_components": list(positive_ratios),
                      "scope": "public example or user input; not a benchmark reproduction"}, indent=2))


if __name__ == "__main__":
    main()

