"""Generate reviewable variants from a user-owned text skill package."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from skilltrace.variants import OFFLINE, LLM, generate

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--families', nargs='+', choices=OFFLINE + LLM, default=list(OFFLINE))
    parser.add_argument('--rng-seed', type=int, default=17)
    parser.add_argument('--model')
    parser.add_argument('--language')
    args = parser.parse_args()
    try:
        result = generate(args.seed, args.output, args.families, args.rng_seed, args.model, args.language)
        print(json.dumps({'pairs': len(result['pairs']), 'utility_review': 'pending'}, indent=2))
    except Exception as exc:
        # Do not echo provider response bodies, credentials, or source contents.
        sys.exit(f'Generation failed ({type(exc).__name__}). Check input format, output directory and provider configuration.')
