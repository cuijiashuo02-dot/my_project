from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from corr import load_config, pearson_correlation, read_columns


BASE = Path(__file__).resolve().parents[1]


class CorrelationTests(unittest.TestCase):
    def test_positive(self):
        result = pearson_correlation([1, 2, 3], [2, 4, 6])
        self.assertAlmostEqual(result, 1.0)

    def test_negative(self):
        result = pearson_correlation([1, 2, 3], [6, 4, 2])
        self.assertAlmostEqual(result, -1.0)

    def test_zero(self):
        result = pearson_correlation([-1, 0, 1], [1, -2, 1])
        self.assertAlmostEqual(result, 0.0)

    def test_constant(self):
        cases = [
            ([1, 1, 1], [2, 4, 6]),
            ([1, 2, 3], [5, 5, 5]),
        ]
        for xs, ys in cases:
            with self.subTest(xs=xs, ys=ys):
                with self.assertRaises(ValueError):
                    pearson_correlation(xs, ys)

    def test_invalid_vectors(self):
        cases = [
            ([], []),
            ([1], [2]),
            ([1, 2], [3]),
            ([1, float("nan")], [2, 3]),
            ([1, float("inf")], [2, 3]),
        ]
        for xs, ys in cases:
            with self.subTest(xs=xs, ys=ys):
                with self.assertRaises(ValueError):
                    pearson_correlation(xs, ys)

    def test_numpy_agreement(self):
        rng = random.Random(42)

        for count in (2, 3, 40, 100):
            xs = [rng.uniform(-100, 100) for _ in range(count)]
            ys = [rng.uniform(-100, 100) for _ in range(count)]

            expected = float(np.corrcoef(xs, ys)[0, 1])
            actual = pearson_correlation(xs, ys)

            self.assertAlmostEqual(actual, expected, delta=1e-6)

    def test_supplied_sample(self):
        config = load_config(BASE / "config.yaml")
        xs, ys = read_columns(
            BASE / config["input_csv"],
            config["columns"]["x"],
            config["columns"]["y"],
        )

        self.assertEqual(len(xs), 40)
        expected = float(np.corrcoef(xs, ys)[0, 1])
        self.assertAlmostEqual(
            pearson_correlation(xs, ys),
            expected,
            delta=1e-6,
        )

    def test_large_and_small_scales(self):
        for scale in (1e150, 1e-150):
            xs = [scale, 2 * scale, 3 * scale]
            ys = [3 * scale, 2 * scale, scale]

            self.assertAlmostEqual(
                pearson_correlation(xs, ys), -1.0
            )


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)

        self.folder = Path(temp.name)
        self.csv = self.folder / "data.csv"
        self.config = self.folder / "config.yaml"

        self.good_csv = "x,y\n1,2\n2,4\n3,6\n"
        self.good_config = (
            "input_csv: data.csv\n"
            "columns: {x: x, y: y}\n"
        )

        self.csv.write_text(self.good_csv, encoding="utf-8")
        self.config.write_text(
            self.good_config, encoding="utf-8"
        )

    def run_cli(self):
        return subprocess.run(
            [
                sys.executable,
                str(BASE / "corr.py"),
                "--config",
                str(self.config),
            ],
            cwd=self.folder,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_success_from_other_directory(self):
        result = self.run_cli()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("n = 3", result.stdout)
        self.assertAlmostEqual(
            float(result.stdout.split("r =")[-1]), 1.0
        )
        self.assertEqual(result.stderr, "")

    def test_error_inputs(self):
        cases = [
            ("空CSV", "", self.good_config),
            ("只有表头", "x,y\n", self.good_config),
            ("缺列", "a,b\n1,2\n2,3\n", self.good_config),
            ("零方差", "x,y\n1,2\n1,3\n", self.good_config),
            ("非数值", "x,y\n1,bad\n2,3\n", self.good_config),
            ("NaN", "x,y\n1,nan\n2,3\n", self.good_config),
            ("字段数错误", "x,y\n1\n2,3\n", self.good_config),
            ("YAML语法错误", self.good_csv, "input_csv: ["),
            ("空YAML", self.good_csv, ""),
            ("配置缺字段", self.good_csv, "input_csv: data.csv\n"),
            ("CSV不存在", None, self.good_config),
            ("YAML不存在", self.good_csv, None),
        ]

        for name, csv_text, config_text in cases:
            with self.subTest(case=name):
                for path, content in [
                    (self.csv, csv_text),
                    (self.config, config_text),
                ]:
                    if content is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.write_text(
                            content, encoding="utf-8"
                        )

                result = self.run_cli()

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("错误", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_verbose_false(self):
        self.config.write_text(
            self.good_config + "task: {verbose: false}\n",
            encoding="utf-8",
        )

        result = self.run_cli()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertTrue(result.stdout.startswith("r ="))
        self.assertAlmostEqual(
            float(result.stdout.split("=", 1)[1]), 1.0
        )

    def test_import_is_quiet(self):
        code = (
            "import sys; "
            "sys.path.insert(0, sys.argv[1]); "
            "import corr"
        )

        result = subprocess.run(
            [sys.executable, "-c", code, str(BASE)],
            cwd=self.folder,
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()