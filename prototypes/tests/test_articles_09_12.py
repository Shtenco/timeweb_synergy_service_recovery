import unittest

from prototypes.scenarios.article09 import propose_action
from prototypes.scenarios.article10 import backtest_returns
from prototypes.scenarios.article11 import run as run_11, simulate_fault
from prototypes.scenarios.article12 import estimate_cost


class OpsScenarioTests(unittest.TestCase):
    def test_09_operator_only_proposes_allowlisted_actions(self):
        allowed = {"restart api", "read status api"}
        self.assertFalse(propose_action("restart api", allowed)["executed"])
        self.assertFalse(propose_action("delete database", allowed)["allowed"])

    def test_10_lookahead_uses_future_return_and_is_separate_from_safe_signal(self):
        result = backtest_returns([100, 90, 80, 100, 130, 120])
        self.assertGreater(result["lookahead_total_return"], result["lagged_signal_total_return"])
        self.assertEqual(result["safe_signal_observations"], len([100, 90, 80, 100, 130, 120]) - 2)
        with self.assertRaisesRegex(ValueError, "finite"):
            backtest_returns([100, float("nan"), 110])
        with self.assertRaisesRegex(ValueError, "numeric"):
            backtest_returns(["100", 90, 80])

    def test_11_destructive_recovery_waits_for_approval(self):
        self.assertFalse(run_11(seed=9)["real_actions_executed"])
        result = simulate_fault("data_loss", approved=False)
        self.assertEqual(result["status"], "blocked_for_approval")
        self.assertIn("restore_snapshot", result["proposed_actions"])
        self.assertNotIn("restore_snapshot", result["simulated_actions_applied"])
        self.assertFalse(result["real_actions_executed"])

    def test_12_cost_per_thousand_correct_answers(self):
        result = estimate_cost(hourly_cost=2, requests_per_second=10, utilization=0.5, success_rate=0.8, hours=1)
        self.assertEqual(result["total_cost"], 2)
        self.assertAlmostEqual(result["cost_per_1000_correct"], 2 / (10 * 0.5 * 3600 * 0.8) * 1000)
        with self.assertRaisesRegex(ValueError, "finite"):
            estimate_cost(hourly_cost=float("nan"), requests_per_second=10, utilization=0.5, success_rate=0.8, hours=1)


if __name__ == "__main__":
    unittest.main()
