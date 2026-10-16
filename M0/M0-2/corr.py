"""读取配置和 CSV，计算 Pearson 相关系数。"""

import argparse
import csv
import math
from pathlib import Path
import sys

import yaml


def load_config(config_path):
    """读取 YAML，并检查必需字段。"""
    with open(config_path, encoding="utf-8-sig") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("配置为空或格式错误，顶层应为键值映射")

    csv_name = config.get("input_csv")
    if not isinstance(csv_name, str) or not csv_name.strip():
        raise ValueError("input_csv 必须是非空文件路径")

    columns = config.get("columns")
    if not isinstance(columns, dict):
        raise ValueError("配置中缺少 columns 映射")

    for axis in ("x", "y"):
        name = columns.get(axis)
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"columns.{axis} 必须是非空列名")

    task = config.get("task", {})
    if not isinstance(task, dict):
        raise ValueError("task 必须是键值映射")

    if not isinstance(task.get("verbose", True), bool):
        raise ValueError("task.verbose 必须是 true 或 false")

    return config


def read_columns(csv_path, col_x, col_y):
    """读取两列数值，检查空文件、缺列和坏数据。"""
    xs = []
    ys = []

    with open(csv_path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        headers = reader.fieldnames

        if not headers:
            raise ValueError("CSV 文件为空或没有表头")

        if len(headers) != len(set(headers)):
            raise ValueError("CSV 表头含有重复列名")

        for column in (col_x, col_y):
            if column not in headers:
                raise ValueError(
                    f"CSV 缺少列 {column!r}，实际列名为 {headers}"
                )

        for row in reader:
            if None in row or any(
                value is None for value in row.values()
            ):
                raise ValueError(
                    f"CSV 第 {reader.line_num} 行字段数与表头不一致"
                )

            try:
                x = float(row[col_x])
                y = float(row[col_y])
            except (TypeError, ValueError):
                raise ValueError(
                    f"CSV 第 {reader.line_num} 行的选定列包含空值或非数值"
                ) from None

            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError(
                    f"CSV 第 {reader.line_num} 行包含 NaN 或无穷大"
                )

            xs.append(x)
            ys.append(y)

    if not xs:
        raise ValueError("CSV 只有表头，没有数据记录")

    return xs, ys


def pearson_correlation(xs, ys):
    """手写 Pearson 公式，检查长度、样本数和零方差。"""
    if len(xs) != len(ys):
        raise ValueError("两列数据长度必须相同")

    if len(xs) < 2:
        raise ValueError("至少需要两对数据")

    try:
        xs = [float(value) for value in xs]
        ys = [float(value) for value in ys]
    except (TypeError, ValueError, OverflowError):
        raise ValueError("输入必须是有效数值") from None

    if not all(math.isfinite(value) for value in xs + ys):
        raise ValueError("输入不能包含 NaN 或无穷大")

    if min(xs) == max(xs) or min(ys) == max(ys):
        raise ValueError("某一列的方差为零，相关系数无定义")

    n = len(xs)
    mean_x = math.fsum(value / n for value in xs)
    mean_y = math.fsum(value / n for value in ys)

    a = [value - mean_x for value in xs]
    b = [value - mean_y for value in ys]

    if not all(math.isfinite(value) for value in a + b):
        raise ValueError("数据量级过大，请先统一缩小数值量级")

    # 正比例缩放偏差不改变相关系数，可减少平方运算的溢出。
    scale_x = max(abs(value) for value in a)
    scale_y = max(abs(value) for value in b)

    if scale_x == 0 or scale_y == 0:
        raise ValueError("浮点精度不足，请调整数据量级")

    a = [value / scale_x for value in a]
    b = [value / scale_y for value in b]

    dx = math.fsum(value * value for value in a)
    dy = math.fsum(value * value for value in b)
    prod = math.fsum(x * y for x, y in zip(a, b))

    result = prod / (math.sqrt(dx) * math.sqrt(dy))
    return max(-1.0, min(1.0, result))


def main(argv=None):
    """成功返回 0，预期输入错误返回 1。"""
    parser = argparse.ArgumentParser(
        description="计算 CSV 两列的 Pearson 相关系数"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="YAML 配置文件路径，默认 config.yaml",
    )
    args = parser.parse_args(argv)

    try:
        config_path = Path(args.config).expanduser().resolve()
        config = load_config(config_path)

        csv_path = Path(config["input_csv"]).expanduser()
        if not csv_path.is_absolute():
            csv_path = config_path.parent / csv_path

        col_x = config["columns"]["x"]
        col_y = config["columns"]["y"]

        xs, ys = read_columns(csv_path, col_x, col_y)
        result = pearson_correlation(xs, ys)

        if config.get("task", {}).get("verbose", True):
            n = len(xs)
            print("n =", n)
            print("mean_x =", math.fsum(value / n for value in xs))
            print("mean_y =", math.fsum(value / n for value in ys))

        print("r =", result)

    except FileNotFoundError as error:
        print(
            f"错误：文件不存在：{error.filename}",
            file=sys.stderr,
        )
        return 1

    except (
        OSError,
        UnicodeError,
        yaml.YAMLError,
        csv.Error,
        ValueError,
        OverflowError,
    ) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())