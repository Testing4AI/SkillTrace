"""Run the bundled minimal SkillTrace demo."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from skilltrace_core.audit import audit_pair


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    report = audit_pair(ROOT / "examples/minimal/anchor", ROOT / "examples/minimal/candidate")
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

