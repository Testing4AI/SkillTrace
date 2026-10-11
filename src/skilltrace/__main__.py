"""Register once; compare cached traces repeatedly."""
import argparse
import json
from pathlib import Path

from .core import audit, calibrate, canonical, load_package, register


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="SkillTrace: register, audit and calibrate")
    sub = parser.add_subparsers(dest="command", required=True)
    reg = sub.add_parser("register", help="Create a versioned trace cache")
    reg.add_argument("package")
    choice = reg.add_mutually_exclusive_group(required=True)
    choice.add_argument("--sog", help="Validated SOG JSON, produced independently for this package")
    choice.add_argument("--model", help="LLM model for ingestion-time extraction")
    reg.add_argument("--vocabulary", required=True)
    reg.add_argument("--output", required=True)
    reg.add_argument("--min-code-chars", type=int, default=200)
    compare = sub.add_parser("audit", help="Compare two caches without LLM calls")
    compare.add_argument("reference")
    compare.add_argument("candidate")
    compare.add_argument("--thresholds", required=True)
    compare.add_argument("--output")
    cal = sub.add_parser("calibrate", help="Fit thresholds on independent negative pairs")
    cal.add_argument("scores", help="JSON array of pair_id, label=0 and scores")
    cal.add_argument("--evaluation-ids", required=True, help="JSON array used to reject overlapping pair IDs")
    cal.add_argument("--alpha", type=float, default=.05)
    cal.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "register":
            if args.min_code_chars < 1:
                raise ValueError("min-code-chars must be positive")
            files, vocab = load_package(args.package), read(args.vocabulary)
            if args.sog:
                data = read(args.sog)
                graph, origin = data["graph"], data["provenance"]
            else:
                from .ingestion import extract_sog
                graph, origin = extract_sog(files, vocab, args.model)
            result = register(files, graph, vocab, origin, args.min_code_chars)
            save(args.output, result)
            print(canonical({"cache_key": result["cache_key"], "status": "registered"}))
        elif args.command == "audit":
            result = audit(read(args.reference), read(args.candidate), read(args.thresholds))
            if args.output:
                save(args.output, result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            result = calibrate(read(args.scores), args.alpha, read(args.evaluation_ids))
            save(args.output, result)
            print(json.dumps(result, indent=2))
    except (ValueError, KeyError, OSError) as exc:
        # Never print request headers, API keys or provider response bodies.
        parser.exit(2, f"SkillTrace failed: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
