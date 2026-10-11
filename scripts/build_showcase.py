"""Materialize transparent, manually specified SOG fixtures for public examples.

These annotations are authored for demonstration. They are not model outputs
or withheld benchmark annotations. Every quote is validated against its package.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from skilltrace.core import load_package, register
from skilltrace.__main__ import save

ORIGIN = {"kind": "curated_demonstration", "version": "showcase-1",
          "description": "Manual source-supported annotations; no claim of LLM extraction accuracy"}


def form_graph(text):
    numbered = [line[3:] for line in text.splitlines() if line[:2] in {"1.", "2.", "3.", "4.", "5."}]
    entry = next(line for line in text.splitlines() if line.startswith(("Start when", "Accept an")))
    order = next(line for line in text.splitlines() if line.startswith(("The order", "Perform discovery")))
    specs = [
        ("inspect", "pdf_form", "pdf_reader", ["blank_form"], ["field_inventory"]),
        ("validate", "record", "schema_validator", ["record", "field_inventory"], ["validated_record"]),
        ("fill", "pdf_form", "pdf_writer", ["blank_form", "validated_record"], ["filled_form"]),
        ("verify", "filled_form", "pdf_reader", ["filled_form", "validated_record"], ["checked_form"]),
        ("export", "filled_form", "pdf_writer", ["checked_form"], ["output_file"]),
    ]
    blocks = [block(f"b{i}", spec, quote) for i, (spec, quote) in enumerate(zip(specs, numbered), 1)]
    return {"blocks": blocks,
            "activation": [{"intent_role": "fill_form", "required_context": ["blank_form", "record"],
                            "start_block": "b1", "evidence": evidence(entry)}],
            "procedure": [{"from": f"b{i}", "to": f"b{i+1}", "relation": "next",
                           "condition_role": "none", "evidence": evidence(order)} for i in range(1, 5)],
            "resource_flow": resources(blocks)}


def evidence(quote):
    return {"file": "SKILL.md", "quote": quote}


def block(identifier, spec, quote):
    action, obj, tool, inputs, outputs = spec
    return {"id": identifier, "action": action, "object_role": obj,
            "tool_role": tool, "inputs": inputs, "outputs": outputs, "evidence": evidence(quote)}


def resources(blocks):
    result = []
    for b in blocks:
        for relation, roles in (("consumes", b["inputs"]), ("produces", b["outputs"]),
                                ("uses_tool", [] if b["tool_role"] == "none" else [b["tool_role"]])):
            result.extend({"from": b["id"], "to": role, "relation": relation,
                           "evidence": b["evidence"]} for role in roles)
    return result


def watchlist_graph(text):
    # Six explicit prose statements follow the sole H1 heading in every version.
    statements = [s for s in text.split("# ", 1)[1].splitlines()[1:] if s.strip()]
    specs = [
        ("select", "analysis_request", "none", ["instrument"], ["analysis_mode"]),
        ("retrieve", "news_evidence", "news_api", ["instrument"], ["news_observation"]),
        ("load", "watchlist_state", "local_store", [], ["watchlist_state", "watchlist_condition"]),
        ("check", "alert_condition", "monitoring_tool", ["watchlist_state", "watchlist_condition", "market_observation"], ["alert_result"]),
        ("report", "alert_result", "none", ["alert_result"], []),
    ]
    blocks = [block(f"b{i}", spec, quote) for i, (spec, quote) in enumerate(zip(specs, statements[:5]), 1)]
    return {"blocks": blocks,
            "activation": [
                {"intent_role": "analyze_security", "required_context": ["instrument"], "start_block": "b1", "evidence": evidence(statements[0])},
                {"intent_role": "check_alerts", "required_context": [], "start_block": "b3", "evidence": evidence(statements[2])}],
            "procedure": [
                {"from": "b1", "to": "b2", "relation": "bypass", "condition_role": "reduced_analysis_mode", "evidence": evidence(statements[1])},
                {"from": "b3", "to": "b4", "relation": "next", "condition_role": "none", "evidence": evidence(statements[5])},
                {"from": "b4", "to": "b5", "relation": "next", "condition_role": "none", "evidence": evidence(statements[5])}],
            "resource_flow": resources(blocks)}


def main():
    vocab = json.loads((ROOT / "config/showcase_vocabulary.json").read_text())
    packages = [("form", "seed"), ("form", "paraphrase"), ("form", "implementation_lift"),
                ("watchlist", "seed"), ("watchlist", "rewrite"), ("watchlist", "translation")]
    for family, name in packages:
        files = load_package(ROOT / "examples" / family / name)
        graph = (form_graph if family == "form" else watchlist_graph)(files["SKILL.md"])
        save(ROOT / "examples/annotations" / f"{family}_{name}.json", {"provenance": ORIGIN, "graph": graph})
        cache = register(files, graph, vocab, ORIGIN)
        save(ROOT / "examples/cache" / f"{family}_{name}.json", cache)
    print("Built six source-checked demonstration caches (two seeds, four variants).")


if __name__ == "__main__":
    main()

