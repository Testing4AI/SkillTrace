"""Behavioral checks for the public artifact; no benchmark data required."""
import copy
import itertools
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from skilltrace.core import (audit, calibrate, compare_sog, digest, extract_ei, load_package,
                             register, validate_sog, validate_cache)
from skilltrace.ingestion import extract_sog


def read(path):
    return json.loads((ROOT / path).read_text())


class MethodTests(unittest.TestCase):
    def setUp(self):
        self.seed = read("examples/cache/form_seed.json")
        self.rewrite = read("examples/cache/form_paraphrase.json")
        self.tau = read("config/paper_thresholds.json")
        self.watch = read("examples/cache/watchlist_seed.json")
        self.vocab = read("config/showcase_vocabulary.json")

    def test_offline_audit_and_missing_implementation(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
            report = audit(self.seed, self.rewrite, self.tau)
        self.assertIsNone(report["scores"]["implementation"])
        self.assertNotIn("implementation", report["calibrated"])
        self.assertEqual(report["maxfusion"], max(report["calibrated"].values()))
        self.assertEqual(report["scores"]["operational"], 1.0)
        self.assertTrue(report["evidence"]["matched_block_sources"]["reference"])

    def test_code_blocks_in_text_and_markdown(self):
        code = "\n".join(f"target_{i} = transform(record_{i})" for i in range(12))
        for suffix in ("md", "txt"):
            out = extract_ei({"SKILL.md": "# Form", f"references/code.{suffix}": f"```python\n{code}\n```"})
            self.assertTrue(out["implementation"]["applicable"])
            self.assertNotIn("target_0", out["expression"]["tokens"])
            self.assertIn("target_0", out["implementation"]["tokens"])

    def test_graph_node_id_invariance(self):
        graph = copy.deepcopy(self.watch["operational"])
        for b in graph["blocks"]:
            b["id"] = "renamed_" + b["id"]
        for a in graph["activation"]:
            a["start_block"] = "renamed_" + a["start_block"]
        for p in graph["procedure"]:
            p["from"], p["to"] = "renamed_" + p["from"], "renamed_" + p["to"]
        for r in graph["resource_flow"]:
            r["from"] = "renamed_" + r["from"]
        self.assertEqual(compare_sog(self.watch["operational"], graph)[0], 1.0)

    def test_relation_direction_and_condition_matter(self):
        original = self.watch["operational"]
        for kind in ("direction", "condition", "resource"):
            altered = copy.deepcopy(original)
            if kind == "direction":
                p = altered["procedure"][1]
                p["from"], p["to"] = p["to"], p["from"]
            elif kind == "condition":
                altered["procedure"][0]["condition_role"] = "tool_failure"
            else:
                altered["resource_flow"][0]["relation"] = "produces"
            self.assertLess(compare_sog(original, altered)[0], 1.0)

    def test_exact_maximum_matching_with_duplicate_blocks(self):
        from skilltrace.core import block_label
        graph = copy.deepcopy(self.seed["operational"])
        graph["blocks"].append({**graph["blocks"][0], "id": "duplicate"})
        value, parts, _ = compare_sog(self.seed["operational"], graph)
        self.assertAlmostEqual(parts["block"], 5/6)
        self.assertGreater(value, 0)

    def test_symmetric_graph_comparison(self):
        a, b = self.seed["operational"], self.watch["operational"]
        self.assertEqual(compare_sog(a, b)[0], compare_sog(b, a)[0])

    def test_bad_quote_and_vocabulary_rejected(self):
        files = load_package(ROOT / "examples/watchlist/seed")
        for field, value in (("action", "invented_action"), ("evidence", {"file": "SKILL.md", "quote": "invented quote"})):
            graph = copy.deepcopy(self.watch["operational"])
            graph["blocks"][0][field] = value
            with self.assertRaises(ValueError):
                validate_sog(graph, files, self.vocab)

    def test_modified_cache_rejected(self):
        cache = copy.deepcopy(self.seed)
        cache["expression"]["tokens"].append("injected")
        with self.assertRaises(ValueError):
            validate_cache(cache)

    def test_calibration_disjointness_and_percentile(self):
        rows = [{"pair_id": f"n{i}", "label": 0,
                 "scores": {k: i/100 for k in ("expression", "implementation", "operational")}}
                for i in range(1, 101)]
        result = calibrate(rows, evaluation_ids=["heldout"])
        self.assertEqual(result["thresholds"]["operational"], .95)
        with self.assertRaises(ValueError):
            calibrate(rows, evaluation_ids=["n2"])
        rows[0]["label"] = 1
        with self.assertRaises(ValueError):
            calibrate(rows)

    def test_zero_threshold_rejected(self):
        self.tau["thresholds"]["expression"] = 0
        with self.assertRaises(ValueError):
            audit(self.seed, self.rewrite, self.tau)

    def test_llm_ingestion_with_mock_response(self):
        graph = self.watch["operational"]
        data = json.dumps({"model": "mock-model", "choices": [{"message": {"content": json.dumps(graph)}}]}).encode()
        from unittest.mock import MagicMock
        response = MagicMock()
        response.__enter__.return_value.read.return_value = data
        with patch.dict("os.environ", {"SKILLTRACE_LLM_URL": "https://example.invalid/v1/chat/completions", "SKILLTRACE_API_KEY": "mock-credential"}), patch("skilltrace.ingestion.urlopen", return_value=response):
            output, provenance = extract_sog(load_package(ROOT / "examples/watchlist/seed"), self.vocab, "mock-model")
        self.assertEqual(output, graph)
        self.assertEqual(provenance["returned_model"], "mock-model")
        self.assertNotIn("mock-credential", json.dumps(provenance))


if __name__ == "__main__":
    unittest.main()
