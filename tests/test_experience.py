import importlib.util
from pathlib import Path
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("experience_lab", BASE / "scripts/experience_lab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class ExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = lab.load(BASE / "fixtures/adaptive/events.jsonl")
        cls.queries = lab.load(BASE / "fixtures/adaptive/queries.jsonl")

    def test_audit_deduplicates_dual_events(self):
        report = lab.audit(self.events)
        self.assertEqual(report["tool_calls"], 1)
        self.assertEqual(report["call_conflicts"], [])

    def test_feedback_delete_overrides_put(self):
        self.assertEqual(lab.audit(self.events)["feedback_current"]["s1:m1"]["deleted"], True)

    def test_event_id_conflict(self):
        with self.assertRaisesRegex(ValueError, "conflicting duplicate"):
            lab.audit([self.events[0], dict(self.events[0], outcome="failed")])

    def test_time_split_avoids_future_information(self):
        report = lab.evaluate(self.events, self.queries, k=1)
        before, after = report["results"]
        self.assertEqual(before["b1"], before["b2"])
        self.assertEqual(after["b1"][0], "tool:pdf")
        self.assertEqual(after["b2"][0], "tool:export")
        self.assertEqual(after["details"][0]["evidence_count"], 5)

    def test_low_evidence_ignored(self):
        q = self.queries[1]
        self.assertEqual(lab.rank(q, self.events[:6], min_evidence=5)["b1"], lab.rank(q, self.events[:6], min_evidence=5)["b2"])

    def test_version_change_discards_old_evidence(self):
        changed = dict(self.queries[1]); changed["candidates"] = [dict(c, release_digest="v3") for c in changed["candidates"]]
        report = lab.rank(changed, self.events)
        self.assertEqual(report["b1"], report["b2"])

    def test_history_cannot_bypass_relevance_or_permission(self):
        q = dict(self.queries[1]); q["candidates"] = [dict(q["candidates"][1], relevance=0.05), dict(q["candidates"][0], authorized=False)]
        self.assertEqual(lab.rank(q, self.events)["b2"], [])

    def test_invalid_weight(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            lab.evaluate(self.events, self.queries, max_weight=0.5)

    def test_only_direct_attribution_and_task_dedup(self):
        q = self.queries[1]
        doubled = self.events + [dict(self.events[4], event_id="duplicate-copy")]
        self.assertEqual(lab.rank(q, doubled)["details"][0]["evidence_count"], 5)
        indirect = [dict(e, attribution="unknown") if e.get("event_type")=="task/evaluated" else e for e in self.events]
        self.assertEqual(lab.rank(q, indirect)["b1"], lab.rank(q, indirect)["b2"])

    def test_sqlite_offline_record(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "run.sqlite3"
            lab.store(str(target), "audit", BASE / "fixtures/adaptive/events.jsonl", lab.audit(self.events))
            self.assertTrue(target.exists())

    def test_unattributed_feedback_not_success_evidence(self):
        q = self.queries[1]
        only_feedback = [e for e in self.events if e["event_type"].startswith("feedback/")]
        result = lab.rank(q, only_feedback)
        self.assertEqual(result["b1"], result["b2"])


if __name__ == "__main__":
    unittest.main()
