"""Read-only checks for the public file allowlist and example boundaries."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TOP_FILES = {"README.md", "pyproject.toml", ".gitignore"}
TOP_DIRS = {"src", "config", "examples", "scripts", "tests", "docs", "assets", "wild"}
ALLOWED_SUFFIXES = {".py", ".md", ".txt", ".json", ".png", ".csv", ".svg"}
WILD_FILES = {"wild/corpus.csv", "wild/manifest.json", "wild/cases.json", "wild/audit_summary.json"}
WILD_FILES |= {f"wild/sog/{name}.json" for name in
               ("1person", "oneperson", "local-self-healing", "capability-evolver", "vocabulary")}
SHOWCASE = {"form": ("seed", "paraphrase", "implementation_lift"),
            "watchlist": ("seed", "rewrite", "translation")}
EXAMPLE_FILES = {f"examples/{family}/{variant}/SKILL.md" for family, variants in SHOWCASE.items() for variant in variants}
EXAMPLE_FILES |= {f"examples/{folder}/{family}_{variant}.json" for family, variants in SHOWCASE.items()
                  for variant in variants for folder in ("annotations", "cache")}
EXAMPLE_FILES |= {f"examples/form/{variant}/references/writer.txt" for variant in ("seed", "implementation_lift")}
CONFIG_FILES = {"config/paper_thresholds.json", "config/showcase_vocabulary.json"}


def public_files():
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if "__pycache__" in rel.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            if rel.parts[0] in TOP_DIRS:
                raise ValueError(f"Symlink in public tree: {rel}")
            continue
        if not path.is_file():
            continue
        if rel.parts[0] == "examples" and rel.as_posix() not in EXAMPLE_FILES:
            raise ValueError(f"Unapproved data in example tree: {rel}")
        if rel.parts[0] == "config" and rel.as_posix() not in CONFIG_FILES:
            raise ValueError(f"Unapproved configuration: {rel}")
        if rel.parts[0] == "wild" and rel.as_posix() not in WILD_FILES:
            raise ValueError(f"Unapproved wild data: {rel}")
        if rel.as_posix() in TOP_FILES or (rel.parts[0] in TOP_DIRS and path.suffix in ALLOWED_SUFFIXES):
            yield path


def check():
    files = list(public_files())
    problems = []
    # Patterns encode categories rather than any researcher's identity.
    sensitive = [r"/(?:Users|home)/[A-Za-z0-9_.-]+/", r"sk-[A-Za-z0-9]{20,}",
                 r"(?i)Bearer\s+[A-Za-z0-9_-]{20,}",
                 r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"]
    patterns = [re.compile(x) for x in sensitive]
    for path in files:
        rel = path.relative_to(ROOT)
        if path.suffix == ".png":
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern.search(text):
                problems.append(f"Identity/credential-like content in {rel}")
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if target.startswith(("http:", "https:", "#", "mailto:")):
                    continue
                target = target.split("#", 1)[0]
                if not (path.parent / target).exists():
                    problems.append(f"Broken relative link in {rel}: {target}")
    packages = [p for p in files if p.name == "SKILL.md"]
    expected = {f"examples/{family}/{variant}/SKILL.md" for family, variants in
                (("form", ("seed", "paraphrase", "implementation_lift")),
                 ("watchlist", ("seed", "rewrite", "translation"))) for variant in variants}
    if {p.relative_to(ROOT).as_posix() for p in packages} != expected:
        problems.append("Example package list differs from the six-file explicit showcase allowlist")
    for folder in ("annotations", "cache"):
        if len(list((ROOT / "examples" / folder).glob("*.json"))) != 6:
            problems.append(f"Expected exactly six example {folder} files")
    from verify_wild_inventory import verify
    verify()
    if problems:
        raise ValueError("\n".join(problems))
    return {"status": "pass", "public_files": len(files), "example_packages": len(packages),
            "full_benchmark_included": False, "relative_links": "valid"}


if __name__ == "__main__":
    try:
        print(json.dumps(check(), indent=2))
    except ValueError as exc:
        sys.exit(str(exc))
