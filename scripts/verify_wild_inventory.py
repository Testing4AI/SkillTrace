"""Check public inventory consistency, not unavailable full-source snapshots."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def verify():
    folder = ROOT / 'wild'
    manifest = json.loads((folder / 'manifest.json').read_text())
    rows = list(csv.DictReader((folder / 'corpus.csv').open()))
    ids = {x['corpus_id'] for x in rows}
    assert len(rows) == len(ids) == manifest['records'] == 36446
    assert hashlib.sha256((folder / 'corpus.csv').read_bytes()).hexdigest() == manifest['inventory_sha256']
    assert dict(Counter(x['platform'] for x in rows)) == manifest['platform_counts']
    cases = json.loads((folder / 'cases.json').read_text())
    assert len(cases) == 2
    for case in cases.values():
        assert case['left_id'] in ids and case['right_id'] in ids
        assert case['candidate_scope'] == 'global'
    import sys
    sys.path.insert(0, str(ROOT / 'src'))
    from skilltrace.core import validate_sog
    vocabulary = json.loads((folder / 'sog/vocabulary.json').read_text())
    for name in ('1person', 'oneperson', 'local-self-healing', 'capability-evolver'):
        record = json.loads((folder / 'sog' / (name + '.json')).read_text())
        graph = record['graph']
        # Schema/reference check against distributed quotations only.
        # The packaging-time source check used the full original file snapshots.
        quotes = {}
        for rows in graph.values():
            for item in rows:
                ev = item['evidence']
                assert ev['line_start'] > 0 and ev['line_end'] >= ev['line_start']
                quotes.setdefault(ev['file'], []).append(ev['quote'])
        validate_sog(graph, {key:'\n'.join(value) for key,value in quotes.items()}, vocabulary)
        assert record['extraction']['full_operational_score'] is None
    audit = json.loads((folder / 'audit_summary.json').read_text())
    for key in ('wild_conservative_count', 'strict_calibrated_count'):
        assert sum(int(row[key]) for row in audit['bucket_counts']) == audit['counts']['global_scored_pairs'] == 204386
    return {'records': len(rows), 'observed_cases': len(cases), 'status': 'pass'}

if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
