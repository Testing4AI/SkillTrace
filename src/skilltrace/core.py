"""Paper-aligned trace representation, deterministic comparison and fusion.

No model call or source-code execution occurs in this module.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

VERSION = "skilltrace.trace.v2"
TEXT_SUFFIXES = {".md", ".txt", ".rst", ".py", ".js", ".ts", ".tsx", ".jsx",
                 ".sh", ".bash", ".json", ".yaml", ".yml", ".toml", ".sql",
                 ".java", ".go", ".rs", ".c", ".cpp", ".h", ".rb"}
DOC_SUFFIXES = {".md", ".txt", ".rst"}
SKIP = {".git", ".venv", "node_modules", "__pycache__", "outputs", "results"}
TOKEN = re.compile(r"[^\W\d_][\w./:-]*|--?[A-Za-z][\w-]*", re.UNICODE)
FENCE = re.compile(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n(.*?)^\s*\1\s*$")
INLINE = re.compile(r"`([^`\n]+)`")
COMMAND = re.compile(r"(?m)^\s*\$\s+(.+)$")
STOPWORDS = set("the a an and or for with that this from into your you are is be to of in on "
                "it its as by at we our can should must when then where also such have has "
                "all any each their there use using skill skills description name workflow "
                "instructions example examples step steps implementation overview".split())


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def load_package(root):
    root = Path(root).resolve()
    if not (root / "SKILL.md").is_file():
        raise ValueError("Package must contain SKILL.md")
    files = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if path.is_symlink() or any(p in SKIP or p.startswith(".") for p in rel.parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            if path.stat().st_size > 2_000_000:
                raise ValueError(f"Text file exceeds 2 MB input limit: {rel}")
            files[rel.as_posix()] = path.read_text(encoding="utf-8")
    return files


def tokens(text, expression=False):
    found = {m.group().lower().strip("./:") for m in TOKEN.finditer(text)}
    return sorted(found - STOPWORDS if expression else found)


def extract_ei(files, min_code_chars=200):
    prose, code, pointers = [], [], []
    for name, text in files.items():
        if Path(name).suffix.lower() in DOC_SUFFIXES:
            for match in FENCE.finditer(text):
                code.append(match[2])
                pointers.append({"file": name, "line": text[:match.start()].count("\n") + 1,
                                 "kind": "fenced_code"})
            body = FENCE.sub(" ", text)
            # Inline executable fragments and explicitly marked command recipes.
            fragments = [m[1] for m in INLINE.finditer(body)
                         if re.search(r"[()=]|--[a-zA-Z]|(?:python|node|uv|pip|git|curl)\s", m[1])]
            fragments.extend(m[1] for m in COMMAND.finditer(body))
            code.extend(fragments)
            if fragments:
                pointers.append({"file": name, "kind": "inline_code_or_command"})
            prose.append(re.sub(r"(?m)^\s*#{1,6}\s+|[*_>|]", " ", body))
        else:
            code.append(text)
            pointers.append({"file": name, "kind": "support_code_or_configuration"})
    joined = "\n".join(code).strip()
    return {"expression": {"tokens": tokens("\n".join(prose), True),
                            "files": [p for p in files if Path(p).suffix.lower() in DOC_SUFFIXES]},
            "implementation": {"tokens": tokens(joined), "code_chars": len(joined),
                               "applicable": len(joined) >= min_code_chars,
                               "pointers": pointers}}


def validate_sog(graph, files, vocabulary):
    """Reject invented enums, dangling edges and unsupported quote pointers.

    Quote occurrence is checked; semantic correctness still needs inspection.
    """
    for key in ("blocks", "activation", "procedure", "resource_flow"):
        if not isinstance(graph.get(key), list):
            raise ValueError(f"SOG requires a list: {key}")
    if not graph["blocks"]:
        raise ValueError("Empty Operational Trace: supply a supported SOG")
    ids = [b.get("id") for b in graph["blocks"]]
    if any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("Block IDs must be nonempty and unique")

    def enum(value, group):
        if value not in vocabulary[group]:
            raise ValueError(f"Unknown {group} role: {value}")

    def roles(values, group):
        if not isinstance(values, list):
            raise ValueError(f"Expected a role list: {group}")
        for value in values:
            enum(value, group)

    def evidence(item):
        ev = item.get("evidence", {})
        if not ev.get("quote") or ev.get("file") not in files or ev["quote"] not in files[ev["file"]]:
            raise ValueError("Every SOG item needs an exact quote in its named source file")

    for b in graph["blocks"]:
        for field in ("action", "object_role", "tool_role"):
            enum(b.get(field), field)
        roles(b.get("inputs"), "artifact_role")
        roles(b.get("outputs"), "artifact_role")
        evidence(b)
    for a in graph["activation"]:
        enum(a.get("intent_role"), "intent_role")
        roles(a.get("required_context"), "artifact_role")
        if a.get("start_block") not in ids:
            raise ValueError("Dangling activation entry")
        evidence(a)
    for p in graph["procedure"]:
        if p.get("from") not in ids or p.get("to") not in ids:
            raise ValueError("Dangling procedure relation")
        enum(p.get("relation"), "procedure_relation")
        enum(p.get("condition_role"), "condition_role")
        evidence(p)
    for r in graph["resource_flow"]:
        enum(r.get("relation"), "resource_relation")
        relation = r["relation"]
        if r.get("from") not in ids:
            raise ValueError("Resource relations must originate at a block")
        enum(r.get("to"), "tool_role" if relation == "uses_tool" else "artifact_role")
        evidence(r)
    return graph


def register(files, graph, vocabulary, extraction, min_code_chars=200):
    validate_sog(graph, files, vocabulary)
    config = {"version": VERSION, "vocabulary": vocabulary,
              "extractor": extraction, "implementation_min_chars": min_code_chars}
    result = {"schema": VERSION, "source_digest": digest(files),
              "config_digest": digest(config), "config": config,
              "operational": graph, **extract_ei(files, min_code_chars),
              "repository_tokens": tokens("\n\n".join(files.values()))}
    result["cache_key"] = digest([result["source_digest"], result["config_digest"]])
    result["integrity"] = digest(result)
    return result


def validate_cache(trace):
    payload = {k: v for k, v in trace.items() if k != "integrity"}
    if trace.get("schema") != VERSION or trace.get("integrity") != digest(payload):
        raise ValueError("Unsupported or modified trace cache; re-register the package")


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a or b else 0.0


def block_label(block):
    return canonical([block["action"], block["object_role"], block["tool_role"],
                      sorted(set(block["inputs"])), sorted(set(block["outputs"]))])


def lcs(left, right):
    if not left or not right:
        return 0.0
    prev = [0] * (len(right) + 1)
    for a in left:
        cur = [0]
        for j, b in enumerate(right, 1):
            cur.append(prev[j-1] + 1 if a == b else max(prev[j], cur[-1]))
        prev = cur
    return prev[-1] / max(len(left), len(right))


def graph_features(graph):
    labels = {b["id"]: block_label(b) for b in graph["blocks"]}
    order = [labels[b["id"]] for b in graph["blocks"]]
    activation = set()
    for a in graph["activation"]:
        activation.add(canonical([a["intent_role"], sorted(a["required_context"]), labels[a["start_block"]]]))
    procedure = {canonical([labels[e["from"]], e["relation"], e["condition_role"], labels[e["to"]]])
                 for e in graph["procedure"]}
    resource = {canonical([labels[e["from"]], e["relation"], e["to"]])
                for e in graph["resource_flow"]}
    return order, activation, procedure, resource


def compare_sog(left, right):
    l, a, p, r = graph_features(left)
    m, b, q, s = graph_features(right)
    # Maximum one-to-one matching for equality of normalized five-field labels.
    matched = sum((Counter(l) & Counter(m)).values()) / max(len(l), len(m))
    sequence = lcs(l, m)
    parts = {"block": .8 * matched + .2 * sequence,
             "activation": jaccard(a, b),
             "procedure": .7 * jaccard(p, q) + .3 * sequence,
             "resource_flow": jaccard(r, s)}
    score = sum(parts[k] * w for k, w in zip(parts, (.30, .10, .40, .20)))
    evidence = {"blocks": sorted(set(l) & set(m)),
                "activation": sorted(a & b), "procedure": sorted(p & q),
                "resource_flow": sorted(r & s)}
    return score, parts, evidence


def compare(left, right):
    validate_cache(left)
    validate_cache(right)
    if left["config"]["vocabulary"] != right["config"]["vocabulary"]:
        raise ValueError("SOG vocabularies differ; register with the same vocabulary")
    if left["config"]["implementation_min_chars"] != right["config"]["implementation_min_chars"]:
        raise ValueError("Implementation applicability settings differ")
    if left["config"]["extractor"] != right["config"]["extractor"]:
        raise ValueError("Extractor configurations differ; use a frozen configuration")
    applicable = left["implementation"]["applicable"] and right["implementation"]["applicable"]
    operational, parts, matched = compare_sog(left["operational"], right["operational"])
    return {"scores": {"expression": jaccard(left["expression"]["tokens"], right["expression"]["tokens"]),
                       "implementation": jaccard(left["implementation"]["tokens"], right["implementation"]["tokens"]) if applicable else None,
                       "operational": operational},
            "implementation_applicable": applicable,
            "operational_components": parts,
            "baselines": {"repo_jaccard": jaccard(left["repository_tokens"], right["repository_tokens"])},
            "evidence": {"expression_tokens": sorted(set(left["expression"]["tokens"]) & set(right["expression"]["tokens"])),
                         "implementation_tokens": sorted(set(left["implementation"]["tokens"]) & set(right["implementation"]["tokens"])) if applicable else [],
                         "sog_matches": {k: [readable_feature(v) for v in values] for k, values in matched.items()},
                         "matched_block_sources": {
                             side: [{"id": b["id"], "fields": {k: b[k] for k in ("action", "object_role", "tool_role", "inputs", "outputs")},
                                     "evidence": b["evidence"]}
                                    for b in cache["operational"]["blocks"]
                                    if block_label(b) in matched["blocks"]]
                             for side, cache in (("reference", left), ("candidate", right))}}}


def readable_feature(value):
    if isinstance(value, str) and value.startswith("["):
        return readable_feature(json.loads(value))
    if isinstance(value, list):
        return [readable_feature(x) for x in value]
    return value


def audit(left, right, thresholds):
    report = compare(left, right)
    tau = thresholds["thresholds"]
    beta = thresholds.get("decision_bound", 1.0)
    if not math.isfinite(beta) or beta <= 0:
        raise ValueError("Decision bound must be finite and positive")
    ratios = {}
    for key, score in report["scores"].items():
        if score is None:
            continue
        threshold = tau.get(key)
        if threshold is None or not math.isfinite(threshold) or threshold <= 0:
            raise ValueError(f"A positive calibrated threshold is required for {key}")
        ratios[key] = score / threshold
    report.update(calibrated=ratios, maxfusion=max(ratios.values()), decision_bound=beta,
                  linear_fusion=sum(ratios.values()) / len(ratios),
                  fired_traces=[key for key, value in ratios.items() if value >= beta],
                  surfaced=max(ratios.values()) >= beta,
                  threshold_source=thresholds.get("source", "user supplied"))
    return report


def calibrate(rows, alpha=.05, evaluation_ids=()):
    """Nearest-rank empirical quantile on an explicitly independent negative set."""
    if not 0 < alpha < 1 or not rows:
        raise ValueError("Need calibration rows and 0 < alpha < 1")
    ids = [r["pair_id"] for r in rows]
    if len(set(ids)) != len(ids) or set(ids) & set(evaluation_ids):
        raise ValueError("Duplicate or overlapping calibration/evaluation pair IDs")
    if any(r.get("label") != 0 for r in rows):
        raise ValueError("Calibration requires independently labelled negatives (label=0)")
    thresholds, counts = {}, {}
    for trace in ("expression", "implementation", "operational"):
        values = sorted(r["scores"][trace] for r in rows if r["scores"].get(trace) is not None)
        if not values or any(not math.isfinite(v) or not 0 <= v <= 1 for v in values):
            raise ValueError(f"Need valid applicable calibration scores for {trace}")
        value = values[math.ceil((1-alpha) * len(values))-1]
        if value <= 0:
            raise ValueError(f"Zero {trace} quantile cannot normalize a ratio; revise the calibration set")
        thresholds[trace], counts[trace] = value, len(values)
    return {"thresholds": thresholds, "decision_bound": 1.0, "alpha": alpha,
            "source": "independent user-supplied calibration negatives",
            "quantile": "nearest-rank empirical", "applicable_counts": counts,
            "calibration_pair_ids": ids}
