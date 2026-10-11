"""Run four offline comparisons and write inspectable reports."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from skilltrace.__main__ import read, save
from skilltrace.core import audit, load_package, digest

PAIRS = [("form", "paraphrase"), ("form", "implementation_lift"),
         ("watchlist", "rewrite"), ("watchlist", "translation")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "outputs/demo"))
    args = parser.parse_args()
    thresholds = read(ROOT / "config/paper_thresholds.json")
    print("Illustrative examples; values below are not benchmark results.\n")
    print("Pair                          Repo-Jac      E       I       O     Max")
    results = []
    for family, variant in PAIRS:
        caches = []
        for name in ("seed", variant):
            cache = read(ROOT / "examples/cache" / f"{family}_{name}.json")
            if cache["source_digest"] != digest(load_package(ROOT / "examples" / family / name)):
                raise ValueError("Example source changed: rebuild its cache")
            caches.append(cache)
        result = audit(*caches, thresholds)
        result["pair"] = f"{family}/{variant}"
        result["scope"] = "curated public demonstration, not a benchmark measurement"
        save(Path(args.output) / f"{family}_{variant}.json", result)
        s = result["scores"]
        impl = "n/a" if s["implementation"] is None else f"{s['implementation']:.3f}"
        print(f"{result['pair']:29} {result['baselines']['repo_jaccard']:7.3f}  {s['expression']:6.3f} {impl:>7}  {s['operational']:6.3f}  {result['maxfusion']:6.3f}")
        results.append(result)
    save(Path(args.output) / "summary.json", results)
    print("\nDetailed reports contain firing traces, SOG components and source quotes.")


if __name__ == "__main__":
    main()

