from __future__ import annotations

import csv
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from redrob.config import load_scoring_config
from redrob.features.career import hidden_gem_score
from redrob.features.disqualifiers import disqualifier_features
from redrob.jd import load_job
from redrob.pipeline import rank_candidates
from redrob.submission import write_submission
from validate_submission import validate

ROOT = Path(__file__).resolve().parents[1]


class RankerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidates = json.loads((ROOT / "data" / "sample_candidates.json").read_text(encoding="utf-8"))

    def test_hidden_gem_detects_backend_search_evidence(self):
        candidate = next(item for item in self.candidates if item["candidate_id"] == "RR-1842")
        self.assertGreater(hidden_gem_score(candidate, load_job()), 0.6)

    def test_consulting_only_is_hard_disqualifier(self):
        candidate = next(item for item in self.candidates if item["candidate_id"] == "RR-6002")
        result = disqualifier_features(candidate, load_job(), load_scoring_config()["career"])
        self.assertIn("consulting_only", result["disqualifier_flags"])
        self.assertTrue(result["hard_disqualified"])

    def test_rank_order_is_deterministic_and_semantic(self):
        first = rank_candidates(self.candidates, len(self.candidates))
        second = rank_candidates(self.candidates, len(self.candidates))
        self.assertEqual([row["candidate_id"] for row in first], [row["candidate_id"] for row in second])
        self.assertEqual(first[0]["candidate_id"], "RR-5107")
        self.assertLess(next(row["rank"] for row in first if row["candidate_id"] == "RR-8890"), len(first) + 1)
        self.assertLess(first[0]["score"], 100.000001)

    def test_generated_submission_passes_validator(self):
        expanded = []
        for index in range(12):
            for candidate in self.candidates:
                item = deepcopy(candidate)
                item["candidate_id"] = f"T-{index:02d}-{candidate['candidate_id']}"
                expanded.append(item)
        ranked = rank_candidates(expanded, 100)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "submission.csv"
            write_submission(ranked, output)
            self.assertEqual(validate(output), [])
            with output.open(encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.reader(handle))), 101)


if __name__ == "__main__":
    unittest.main()

