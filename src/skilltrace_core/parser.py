"""Skill package loading utilities.

The loader is intentionally conservative: it reads SKILL.md and small text
support files, skips binary/cache/dependency directories, and keeps paths for
evidence reporting.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".sh",
    ".bash",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".sql",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "datasets",
    "results",
    "outputs",
    "artifacts",
}


@dataclass(frozen=True)
class SkillFile:
    """A text file inside a skill package."""

    path: str
    text: str


@dataclass(frozen=True)
class SkillPackage:
    """Loaded skill package."""

    root: Path
    slug: str
    skill_md: str
    support_files: tuple[SkillFile, ...]
    frontmatter: dict[str, str]

    def all_text(self) -> str:
        parts = [self.skill_md]
        parts.extend(f.text for f in self.support_files)
        return "\n\n".join(parts)


def load_skill_package(root: str | Path, max_file_bytes: int = 512_000) -> SkillPackage:
    """Load a skill package rooted at ``root``.

    A valid package should contain ``SKILL.md``. Support files are optional.
    """

    root_path = Path(root).resolve()
    if not root_path.exists() or not root_path.is_dir():
        raise FileNotFoundError(f"Skill root does not exist or is not a directory: {root_path}")

    skill_md_path = root_path / "SKILL.md"
    if not skill_md_path.exists():
        raise FileNotFoundError(f"Missing SKILL.md under {root_path}")

    skill_md = _read_text(skill_md_path, max_file_bytes=max_file_bytes)
    support_files: list[SkillFile] = []
    for path in _iter_text_files(root_path):
        if path == skill_md_path:
            continue
        if path.stat().st_size > max_file_bytes:
            continue
        try:
            text = _read_text(path, max_file_bytes=max_file_bytes)
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(root_path).as_posix()
        support_files.append(SkillFile(path=rel, text=text))

    return SkillPackage(
        root=root_path,
        slug=root_path.name,
        skill_md=skill_md,
        support_files=tuple(sorted(support_files, key=lambda f: f.path)),
        frontmatter=_parse_frontmatter(skill_md),
    )


def _iter_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(root).parts)
        if parts & SKIP_DIRS:
            continue
        if path.name.startswith("."):
            continue
        if path.suffix.lower() in TEXT_EXTENSIONS:
            yield path


def _read_text(path: Path, max_file_bytes: int) -> str:
    data = path.read_bytes()[:max_file_bytes]
    return data.decode("utf-8")


def _parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip().lower()] = value.strip().strip("\"'")
    return out

