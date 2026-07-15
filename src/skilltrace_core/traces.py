"""Trace extraction for SkillTrace core."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .parser import SkillPackage


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_./:-]{2,}")
FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*\n(.*?)```", re.DOTALL)

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "your",
    "you",
    "are",
    "use",
    "using",
    "will",
    "can",
    "should",
    "must",
    "when",
    "then",
    "where",
    "also",
    "such",
    "have",
    "has",
    "not",
    "all",
    "any",
    "each",
    "their",
    "there",
}

CODE_EXTENSIONS = {
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
    ".sql",
}

ACTION_VOCAB = {
    "parse",
    "validate",
    "retrieve",
    "fetch",
    "transform",
    "analyze",
    "generate",
    "write",
    "execute",
    "verify",
    "report",
    "search",
    "summarize",
    "configure",
    "call",
    "render",
    "test",
}

OBJECT_HINTS = {
    "document": "document",
    "pdf": "document",
    "file": "document",
    "code": "code",
    "script": "code",
    "data": "data",
    "dataset": "data",
    "config": "config",
    "setting": "config",
    "result": "result",
    "report": "report",
    "output": "result",
    "api": "tool_output",
    "response": "tool_output",
}

TOOL_HINTS = {
    "read": "file_reader",
    "file": "file_reader",
    "shell": "shell_runner",
    "command": "shell_runner",
    "bash": "shell_runner",
    "api": "api_client",
    "http": "api_client",
    "browser": "browser",
    "web": "browser",
    "database": "database",
    "sql": "database",
    "test": "test_runner",
    "format": "formatter",
}


@dataclass(frozen=True)
class ExpressionTrace:
    tokens: frozenset[str]
    pointers: tuple[str, ...]


@dataclass(frozen=True)
class ImplementationTrace:
    tokens: frozenset[str]
    code_chars: int
    applicable: bool
    pointers: tuple[str, ...]


@dataclass(frozen=True)
class OperationalBlock:
    block_id: str
    action: str
    object_role: str
    tool_role: str
    label: str


@dataclass(frozen=True)
class OperationalTrace:
    activation: frozenset[str]
    blocks: tuple[OperationalBlock, ...]
    procedure_edges: frozenset[tuple[str, str, str]]
    resource_edges: frozenset[tuple[str, str, str]]


@dataclass(frozen=True)
class TraceBundle:
    expression: ExpressionTrace
    implementation: ImplementationTrace
    operational: OperationalTrace


def extract_traces(package: SkillPackage, implementation_min_chars: int = 200) -> TraceBundle:
    """Extract all three provenance traces from a loaded skill package."""

    expression_text = _strip_code_fences(package.skill_md)
    expression_text += "\n".join(_markdown_support_text(package))
    expression_tokens = frozenset(_tokens(expression_text))

    code_parts = list(_fenced_code(package.skill_md))
    code_pointers = ["SKILL.md:fenced-code"] if code_parts else []
    for support in package.support_files:
        suffix = "." + support.path.rsplit(".", 1)[-1].lower() if "." in support.path else ""
        if suffix in CODE_EXTENSIONS:
            code_parts.append(support.text)
            code_pointers.append(support.path)
    code_text = "\n".join(code_parts)
    impl_tokens = frozenset(_tokens(code_text, keep_stopwords=True))
    code_chars = len(code_text.strip())

    operational = _extract_operational_trace(package)
    return TraceBundle(
        expression=ExpressionTrace(tokens=expression_tokens, pointers=("SKILL.md",)),
        implementation=ImplementationTrace(
            tokens=impl_tokens,
            code_chars=code_chars,
            applicable=code_chars >= implementation_min_chars,
            pointers=tuple(code_pointers),
        ),
        operational=operational,
    )


def _tokens(text: str, keep_stopwords: bool = False) -> list[str]:
    toks = [m.group(0).lower().strip("./:-") for m in TOKEN_RE.finditer(text)]
    if keep_stopwords:
        return [t for t in toks if len(t) >= 3]
    return [t for t in toks if len(t) >= 3 and t not in STOPWORDS]


def _strip_code_fences(text: str) -> str:
    return FENCE_RE.sub(" ", text)


def _fenced_code(text: str) -> list[str]:
    return [m.group(1) for m in FENCE_RE.finditer(text)]


def _markdown_support_text(package: SkillPackage) -> list[str]:
    return [f.text for f in package.support_files if f.path.lower().endswith((".md", ".txt"))]


def _extract_operational_trace(package: SkillPackage, max_blocks: int = 32) -> OperationalTrace:
    text = package.all_text()
    activation = frozenset(_activation_signature(package))
    candidate_lines = _candidate_operation_lines(text)
    blocks: list[OperationalBlock] = []
    for line in candidate_lines:
        block = _line_to_block(len(blocks) + 1, line)
        if block is None:
            continue
        blocks.append(block)
        if len(blocks) >= max_blocks:
            break

    if not blocks:
        blocks = [OperationalBlock("b1", "execute", "input", "none", "execute:input:none")]

    procedure_edges = {
        (blocks[i].label, "next", blocks[i + 1].label)
        for i in range(len(blocks) - 1)
    }
    resource_edges = set()
    for block in blocks:
        if block.tool_role != "none":
            resource_edges.add((block.label, "uses_tool", block.tool_role))
        resource_edges.add((block.object_role, "consumed_by", block.label))
        resource_edges.add((block.label, "produces", _output_role(block)))

    return OperationalTrace(
        activation=activation,
        blocks=tuple(blocks),
        procedure_edges=frozenset(procedure_edges),
        resource_edges=frozenset(resource_edges),
    )


def _activation_signature(package: SkillPackage) -> list[str]:
    fields = []
    for key in ("name", "description", "when_to_use", "when to use"):
        if key in package.frontmatter:
            fields.append(package.frontmatter[key])

    lines = package.skill_md.splitlines()
    for i, line in enumerate(lines):
        lower = line.lower()
        if any(marker in lower for marker in ("when to use", "trigger", "use this skill", "use when")):
            fields.extend(lines[i : i + 4])
    if not fields:
        fields = lines[:12]
    toks = _tokens("\n".join(fields))
    return sorted(set(toks))[:24]


def _candidate_operation_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip(" \t-*#0123456789.").strip()
        if len(line) < 12 or len(line) > 220:
            continue
        lower = line.lower()
        if any(verb in lower for verb in ACTION_VOCAB) or re.match(r"^(read|load|call|run|check|create)\b", lower):
            lines.append(line)
    return lines


def _line_to_block(index: int, line: str) -> OperationalBlock | None:
    lower_tokens = _tokens(line, keep_stopwords=True)
    action = _choose_role(lower_tokens, ACTION_VOCAB, default="execute")
    object_role = _choose_from_hints(lower_tokens, OBJECT_HINTS, default="input")
    tool_role = _choose_from_hints(lower_tokens, TOOL_HINTS, default="none")
    label = f"{action}:{object_role}:{tool_role}"
    return OperationalBlock(
        block_id=f"b{index}",
        action=action,
        object_role=object_role,
        tool_role=tool_role,
        label=label,
    )


def _choose_role(tokens: list[str], vocab: set[str], default: str) -> str:
    for tok in tokens:
        if tok in vocab:
            return tok
    return default


def _choose_from_hints(tokens: list[str], hints: dict[str, str], default: str) -> str:
    for tok in tokens:
        for hint, role in hints.items():
            if hint in tok:
                return role
    return default


def _output_role(block: OperationalBlock) -> str:
    if block.action in {"report", "write", "generate", "render"}:
        return "report"
    if block.action in {"validate", "verify", "test"}:
        return "validation_artifact"
    if block.action in {"retrieve", "fetch", "call", "search"}:
        return "tool_output"
    return "intermediate_result"

