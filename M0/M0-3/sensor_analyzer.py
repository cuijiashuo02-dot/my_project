#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sensor_analyzer.py  —— 上一届学长留下的"能用"的脚本

注释（学长原话）：
    "处理一下传感器数据就能用"

原本意图：
    1. 读取 sensor_data.csv（列：time, value）
    2. 计算 value 的平均值、标准差
    3. 剔除离群值（|value - mean| > 2 * std）
    4. 把清洗后的数据保存为 cleaned_data.csv
    5. 打印一份统计摘要

现状：跑不通 / 跑出来数不对。就交给你了。
"""
import argparse
import csv
import math
import sys


def fail(message):
    print(f"错误：{message}", file=sys.stderr)
    sys.exit(1)

parser = argparse.ArgumentParser(
    description="读取传感器 CSV，按两倍总体标准差清洗数据。"
)

parser.add_argument(
    "--input",
    default="sensor_data.csv",
    help="输入 CSV 路径，默认 sensor_data.csv",
)

parser.add_argument(
    "--output",
    default="cleaned_data.csv",
    help="输出 CSV 路径，默认 cleaned_data.csv",
)

args = parser.parse_args()

INPUT_FILE = args.input
OUTPUT_FILE = args.output

data = []
times = []
cleaned = []

print("=== 传感器数据分析 ===")

# --- 读取数据 ---
# --- 读取数据 ---
try:
    with open(INPUT_FILE, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, strict=True)
        headers = reader.fieldnames

        if headers is None:
            fail("输入文件为空，缺少 time,value 表头。")

        if "time" not in headers or "value" not in headers:
            fail("CSV 必须包含 time 和 value 两列，请检查列名大小写。")

        for row in reader:
            line_number = reader.line_num

            if None in row or any(item is None for item in row.values()):
                fail(f"第 {line_number} 行的字段数量与表头不一致。")

            try:
                t = float(row["time"])
                v = float(row["value"])
            except (ValueError, TypeError):
                fail(f"第 {line_number} 行的 time 或 value 不是有效数字。")

            if not math.isfinite(t) or not math.isfinite(v):
                fail(f"第 {line_number} 行包含 NaN 或无穷大。")

            times.append(t)
            data.append(v)

except (OSError, UnicodeError, csv.Error) as exc:
    fail(f"读取输入文件失败：{exc}")

if not data:
    fail("输入文件没有可分析的数据行。")

print("共读取 %d 条数据" % len(data))

# --- 计算平均值 ---
total = 0
for v in data:
    total += v
mean = total / len(data)

# --- 计算标准差 ---
acc = 0
for v in data:
    acc += (v - mean) ** 2
std = (acc / len(data)) ** 0.5

# --- 剔除离群值 ---
# --- 剔除离群值，同时保留对应时间 ---
for t, v in zip(times, data):
    if abs(v - mean) <= 2 * std:
        cleaned.append((t, v))

# --- 输出清洗后的数据 ---
output_path = OUTPUT_FILE
# --- 输出清洗后的数据 ---
# --- 输出清洗后的数据 ---
output_path = OUTPUT_FILE

try:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "value"])

        for t, v in cleaned:
            writer.writerow([t, v])

except (OSError, UnicodeError, csv.Error) as exc:
    fail(f"写入输出文件失败：{exc}")

print("均值 mean = %.4f" % mean)
print("标准差 std = %.4f" % std)
print("清洗后剩余 %d 条" % len(cleaned))
print("已保存到 %s" % output_path)
