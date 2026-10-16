"""读取配置和数据，计算 Pearson 相关系数。"""
import argparse
import csv
import math
from pathlib import Path

import yaml


def load_config(config_path):
    """读取 YAML 配置，返回字典。"""
    with open(config_path, encoding="utf-8-sig") as file:
        return yaml.safe_load(file)


def read_columns(csv_path, col_x, col_y):
    """读取指定的两列，返回两个数值列表。"""
    xs = []
    ys = []

    with open(csv_path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            xs.append(float(row[col_x]))
            ys.append(float(row[col_y]))

    return xs, ys


def pearson_correlation(xs, ys):
    """手写 Pearson 相关系数的计算公式。"""
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    dx = 0.0
    dy = 0.0
    prod = 0.0

    for x, y in zip(xs, ys):
        a = x - mean_x
        b = y - mean_y

        dx += a * a
        dy += b * b
        prod += a * b

    return prod / math.sqrt(dx * dy)


def main():
    """解析命令行参数，并组织程序的执行顺序。"""
    parser = argparse.ArgumentParser(
        description="计算 CSV 两列的 Pearson 相关系数"
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="YAML 配置文件路径，默认 config.yaml",
    )

    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)

    csv_path = Path(config["input_csv"])

    if not csv_path.is_absolute():
        csv_path = config_path.parent / csv_path

    col_x = config["columns"]["x"]
    col_y = config["columns"]["y"]

    xs, ys = read_columns(csv_path, col_x, col_y)
    result = pearson_correlation(xs, ys)

    print("n =", len(xs))
    print("mean_x =", sum(xs) / len(xs))
    print("mean_y =", sum(ys) / len(ys))
    print("r =", result)


if __name__ == "__main__":
    main()