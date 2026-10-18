import unittest
from unittest.mock import patch

from scheduler import TaskScheduler


def make_task(name, rate=1.0, deps=None):
    return {
        "name": name,
        "duration": 0,
        "success_rate": rate,
        "dependencies": deps or [],
    }


class ExecutionTests(unittest.TestCase):
    def test_failure_skip_and_independent_task(self):
        tasks = [
            make_task("Fail", 0),
            make_task("Child", deps=["Fail"]),
            make_task("Grandchild", deps=["Child"]),
            make_task("Independent"),
            make_task("Join", deps=["Child", "Independent"]),
        ]

        runner = TaskScheduler(tasks, seed=42)

        with patch.object(runner, "log"):
            results = runner.run()

        self.assertEqual(len(results), 5)
        self.assertEqual(results["Fail"]["status"], "FAILED")
        self.assertEqual(results["Fail"]["attempts"], 3)

        for name in ["Child", "Grandchild", "Join"]:
            self.assertEqual(results[name]["status"], "SKIPPED")
            self.assertEqual(results[name]["attempts"], 0)
            self.assertIsNone(results[name]["started_at"])

        self.assertEqual(results["Independent"]["status"], "SUCCESS")
        self.assertEqual(results["Independent"]["attempts"], 1)

    def test_third_attempt_can_succeed(self):
        runner = TaskScheduler([make_task("Retry", 0.5)])

        with patch.object(runner, "log"):
            with patch.object(
                runner.rng,
                "random",
                side_effect=[0.9, 0.8, 0.1],
            ):
                results = runner.run()

        self.assertEqual(results["Retry"]["status"], "SUCCESS")
        self.assertEqual(results["Retry"]["attempts"], 3)

    def test_seed_reproduces_status_and_attempts(self):
        tasks = [
            make_task("A", 0.5),
            make_task("B", 0.7, ["A"]),
            make_task("C", 0.4),
        ]

        signatures = []

        for _ in range(2):
            runner = TaskScheduler(tasks, seed=42)

            with patch.object(runner, "log"):
                results = runner.run()

            signatures.append({
                name: (record["status"], record["attempts"])
                for name, record in results.items()
            })

        self.assertEqual(signatures[0], signatures[1])


if __name__ == "__main__":
    unittest.main()