import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import yaml


class AcceptanceTests(unittest.TestCase):
    def check_report(self, report, expected_names):
        self.assertTrue(
            {"timeout", "total_duration", "tasks"} <= report.keys()
        )
        self.assertIsInstance(report["timeout"], bool)
        self.assertGreaterEqual(report["total_duration"], 0)

        rows = report["tasks"]
        self.assertEqual(len(rows), len(expected_names))
        self.assertEqual(
            {row["name"] for row in rows},
            expected_names,
        )

        fields = {
            "name", "status", "attempts",
            "duration", "started_at", "ended_at",
        }

        for row in rows:
            self.assertTrue(fields <= row.keys())
            self.assertIn(
                row["status"],
                {"SUCCESS", "FAILED", "SKIPPED", "TIMEOUT"},
            )
            self.assertIs(type(row["attempts"]), int)
            self.assertGreaterEqual(row["attempts"], 0)
            self.assertLessEqual(row["attempts"], 3)

    def test_final_acceptance(self):
        script = Path("scheduler.py").resolve()

        with open("tasks_demo.json", encoding="utf-8-sig") as f:
            base = json.load(f)

        expected_names = {task["name"] for task in base["tasks"]}

        # 创建快速测试副本，不修改官方文件。
        for task in base["tasks"]:
            task["duration"] = 0
            task["success_rate"] = 1.0
        base["timeout"] = 2

        normal = deepcopy(base)
        normal["tasks"].reverse()

        unknown = deepcopy(base)
        unknown["tasks"][0]["dependencies"] = ["MissingTask"]

        cycle = deepcopy(base)
        cycle["tasks"][0]["dependencies"] = ["ReturnHome"]

        bad_rate = deepcopy(base)
        bad_rate["tasks"][0]["success_rate"] = 1.2

        cases = [
            ("json", json.dumps(normal), ".json", True),
            ("yaml", yaml.safe_dump(normal), ".yaml", True),
            ("yml", yaml.safe_dump(normal), ".yml", True),
            ("missing", None, ".json", False),
            ("syntax_json", "{", ".json", False),
            ("syntax_yaml", "tasks: [", ".yaml", False),
            ("empty_tasks", '{"tasks": []}', ".json", False),
            ("unknown", json.dumps(unknown), ".json", False),
            ("cycle", json.dumps(cycle), ".json", False),
            ("bad_rate", json.dumps(bad_rate), ".json", False),
        ]

        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)

            for name, text, suffix, valid in cases:
                with self.subTest(case=name):
                    config_path = folder / f"{name}{suffix}"
                    report_path = folder / f"{name}_report.json"

                    if text is not None:
                        config_path.write_text(text, encoding="utf-8")

                    result = subprocess.run(
                        [
                            sys.executable, str(script),
                            "--config", str(config_path),
                            "--report", str(report_path),
                            "--seed", "42",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )

                    self.assertNotIn(
                        "Traceback",
                        result.stdout + result.stderr,
                    )

                    if not valid:
                        self.assertNotEqual(result.returncode, 0)
                        self.assertTrue(result.stderr.strip())
                        continue

                    self.assertEqual(
                        result.returncode, 0, result.stderr
                    )

                    report = json.loads(
                        report_path.read_text(encoding="utf-8")
                    )
                    self.check_report(report, expected_names)
                    self.assertFalse(report["timeout"])

                    for row in report["tasks"]:
                        self.assertEqual(row["status"], "SUCCESS")
                        self.assertEqual(row["attempts"], 1)

                    positions = {
                        row["name"]: i
                        for i, row in enumerate(report["tasks"])
                    }

                    for task in normal["tasks"]:
                        for dep in task["dependencies"]:
                            self.assertLess(
                                positions[dep],
                                positions[task["name"]],
                            )

                    self.assertNotIn("\033[", result.stdout)

        # 核对准备交付的两份真实报告。
        for path, expected_timeout in [
            ("report.json", False),
            ("docs/timeout_report.json", True),
        ]:
            with self.subTest(report=path):
                report = json.loads(
                    Path(path).read_text(encoding="utf-8")
                )
                self.check_report(report, expected_names)
                self.assertEqual(
                    report["timeout"], expected_timeout
                )


if __name__ == "__main__":
    unittest.main()