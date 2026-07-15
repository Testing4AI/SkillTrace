"""Deterministic attack/reuse transformations for artifact smoke tests.

The paper benchmark used a larger attack suite with LLM-generated variants.
This module provides small deterministic operators so reviewers can inspect the
threat-model mechanics without needing private data or API keys.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .parser import load_skill_package


@dataclass(frozen=True)
class GeneratedAttack:
    family: str
    source: str
    output: str
    expected_preserved_traces: tuple[str, ...]
    expected_weakened_traces: tuple[str, ...]


ATTACK_FAMILIES = {
    "metadata_rewrite",
    "structural_reorg",
    "implementation_lift_doc_rewrite",
    "doc_reuse_impl_rewrite",
    "dilution",
}


def generate_attacks(source_root: str | Path, output_root: str | Path) -> list[GeneratedAttack]:
    source = load_skill_package(source_root)
    out = Path(output_root).resolve()
    out.mkdir(parents=True, exist_ok=True)
    generated = [
        _metadata_rewrite(source.skill_md, source.root, out),
        _structural_reorg(source.skill_md, source.root, out),
        _implementation_lift_doc_rewrite(source.skill_md, source.root, out),
        _doc_reuse_impl_rewrite(source.skill_md, source.root, out),
        _dilution(source.skill_md, source.root, out),
    ]
    return generated


def _metadata_rewrite(skill_md: str, source_root: Path, output_root: Path) -> GeneratedAttack:
    body = _replace_frontmatter(
        skill_md,
        {
            "name": "relocated-form-assistant",
            "description": "Assist with structured form completion and output verification.",
            "when_to_use": "Use when structured records must be merged into a checked document.",
        },
    )
    root = _write_package(output_root / "metadata_rewrite", body)
    return GeneratedAttack(
        "metadata_rewrite",
        str(source_root),
        str(root),
        ("Expression", "Implementation", "Operational"),
        (),
    )


def _structural_reorg(skill_md: str, source_root: Path, output_root: Path) -> GeneratedAttack:
    title, sections = _split_markdown_sections(skill_md)
    reordered = title + "\n\n" + "\n\n".join(reversed(sections))
    root = _write_package(output_root / "structural_reorg", reordered)
    return GeneratedAttack(
        "structural_reorg",
        str(source_root),
        str(root),
        ("Expression", "Implementation", "Operational"),
        ("RepoClone-ssdeep",),
    )


def _implementation_lift_doc_rewrite(
    skill_md: str, source_root: Path, output_root: Path
) -> GeneratedAttack:
    code = "\n\n".join(re.findall(r"```[a-zA-Z0-9_-]*\n.*?```", skill_md, flags=re.DOTALL))
    body = """---
name: enterprise-document-runtime
description: Runtime helper for checked document generation.
when_to_use: Use for document generation tasks that require validation.
---

# Enterprise Document Runtime

This package supports a different product framing, but keeps the executable
runtime pattern for filling and validating generated documents.

## Runtime Core

""" + code + "\n"
    root = _write_package(output_root / "implementation_lift_doc_rewrite", body)
    return GeneratedAttack(
        "implementation_lift_doc_rewrite",
        str(source_root),
        str(root),
        ("Implementation", "Operational"),
        ("Expression",),
    )


def _doc_reuse_impl_rewrite(skill_md: str, source_root: Path, output_root: Path) -> GeneratedAttack:
    prose = re.sub(r"```[a-zA-Z0-9_-]*\n.*?```", _replacement_code_block(), skill_md, flags=re.DOTALL)
    root = _write_package(output_root / "doc_reuse_impl_rewrite", prose)
    return GeneratedAttack(
        "doc_reuse_impl_rewrite",
        str(source_root),
        str(root),
        ("Expression", "Operational"),
        ("Implementation",),
    )


def _dilution(skill_md: str, source_root: Path, output_root: Path) -> GeneratedAttack:
    junk = "\n\n".join(
        f"## Appendix Note {i}\n\n"
        "This generic registry note documents contribution process, release "
        "hygiene, support expectations, and compatibility policy."
        for i in range(1, 16)
    )
    root = _write_package(output_root / "dilution", skill_md + "\n\n" + junk)
    return GeneratedAttack(
        "dilution",
        str(source_root),
        str(root),
        ("Expression", "Implementation", "Operational"),
        ("RepoClone-Jaccard",),
    )


def _replacement_code_block() -> str:
    return """```python
def build_checked_document(template, values, target):
    required = discover_required_fields(template)
    errors = [name for name in required if name not in values]
    if errors:
        raise RuntimeError({"missing": errors})
    document = open_form_template(template)
    document.apply_values(values)
    document.write(target)
    return {"output": target, "status": "ok"}
```"""


def _replace_frontmatter(skill_md: str, fields: dict[str, str]) -> str:
    if not skill_md.startswith("---"):
        header = "---\n" + "\n".join(f"{k}: {v}" for k, v in fields.items()) + "\n---\n\n"
        return header + skill_md
    lines = skill_md.splitlines()
    out = [lines[0]]
    in_frontmatter = True
    seen = set()
    for line in lines[1:]:
        if in_frontmatter and line.strip() == "---":
            for key, value in fields.items():
                if key not in seen:
                    out.append(f"{key}: {value}")
            out.append(line)
            in_frontmatter = False
            continue
        if in_frontmatter and ":" in line:
            key = line.split(":", 1)[0].strip()
            if key in fields:
                out.append(f"{key}: {fields[key]}")
                seen.add(key)
            else:
                out.append(line)
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def _split_markdown_sections(skill_md: str) -> tuple[str, list[str]]:
    parts = re.split(r"(?m)(?=^##\s+)", skill_md)
    if len(parts) == 1:
        return skill_md, []
    return parts[0], parts[1:]


def _write_package(root: Path, skill_md: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "SKILL.md").write_text(skill_md, encoding="utf-8")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic SkillTrace attack variants.")
    parser.add_argument("source")
    parser.add_argument("output_root")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    generated = generate_attacks(args.source, args.output_root)
    print(
        json.dumps(
            [asdict(item) for item in generated],
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

