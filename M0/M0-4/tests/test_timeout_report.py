import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scheduler import TaskScheduler, write_report


def make_task(name, duration=0, deps=None):
    return {
        "name": name,
        "duration": duration,
        "success_rate": 1.0,
        "dependencies": deps or [],
    }


class TimeoutReportTests(unittest.TestCase):
    def test_timeout_interrupts_wait_and_keeps_all_tasks(self):
        tasks = [
            make_task("Long", 10),
            make_task("Next", deps=["Long"]),
        ]
        runner = TaskScheduler(tasks, timeout=1)
        clock = {"now": 0.0}

        def fake_sleep(seconds):
            clock["now"] += seconds

        with patch("scheduler.time.monotonic", lambda: clock["now"]), \
             patch("scheduler.time.time", lambda: 1700000000 + clock["now"]), \
             patch("scheduler.time.sleep", fake_sleep), \
             patch.object(runner, "log"):
            results = runner.run()

        self.assertTrue(runner.timed_out)
        self.assertAlmostEqual(runner.total_duration, 1.0)
        self.assertEqual(len(results), 2)

        self.assertEqual(results["Long"]["status"], "TIMEOUT")
        self.assertEqual(results["Long"]["attempts"], 1)

        self.assertEqual(results["Next"]["status"], "TIMEOUT")
        self.assertEqual(results["Next"]["attempts"], 0)
        self.assertIsNone(results["Next"]["started_at"])

    def test_report_and_plain_text_output(self):
        runner = TaskScheduler([make_task("Init")], seed=42)

        with patch.object(runner, "log"):
            runner.run()

        report = runner.build_report()

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            write_report(report, path)

            with path.open(encoding="utf-8") as f:
                saved = json.load(f)

        self.assertEqual(
            set(saved),
            {"timeout", "total_duration", "tasks"},
        )
        self.assertFalse(saved["timeout"])
        self.assertEqual(len(saved["tasks"]), 1)
        self.assertEqual(
            set(saved["tasks"][0]),
            {
                "name", "status", "attempts",
                "duration", "started_at", "ended_at",
            },
        )

        output = io.StringIO()

        with patch("scheduler.sys.stdout", output):
            runner.log("SUCCESS", "Init", "完成")

        self.assertNotIn("\033[", output.getvalue())


if __name__ == "__main__":
    unittest.main()