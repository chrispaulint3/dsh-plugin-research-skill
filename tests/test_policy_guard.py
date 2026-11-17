import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("policy_guard", ROOT/"scripts/policy_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class PolicyGuardTests(unittest.TestCase):
    def test_all_modes(self):
        for mode in ["off", "observe", "recommend", "enforce"]:
            self.assertEqual(guard.validate({"mode": mode})["mode"], mode)

    def test_recommend_never_shadows(self):
        for mode in ["off", "observe", "recommend"]:
            with self.assertRaisesRegex(ValueError, "only enforce"):
                guard.validate({"mode": mode, "skill": {"catalogShadow": True}})
            with self.assertRaisesRegex(ValueError, "only enforce"):
                guard.validate({"mode": mode, "tool": {"routingEnabled": True}})

    def test_off_means_no_observation(self):
        with self.assertRaisesRegex(ValueError, "off must not"):
            guard.validate({"mode": "off", "collectEvents": True})

    def test_weight_bounded(self):
        with self.assertRaisesRegex(ValueError, "maxHistoryWeight"):
            guard.validate({"mode": "enforce", "learning": {"maxHistoryWeight": 0.30}})

    def test_enforce_can_restrict(self):
        self.assertTrue(guard.validate({"mode":"enforce", "skill":{"catalogShadow":True}})["visibility_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()
