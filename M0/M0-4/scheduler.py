#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_config(config_path):
    """读取 JSON 或 YAML，检查基本结构，返回完整配置。"""
    suffix = Path(config_path).suffix.lower()

    if suffix not in {".json", ".yaml", ".yml"}:
        raise ValueError("配置文件扩展名必须是 .json、.yaml 或 .yml。")

    with open(config_path, "r", encoding="utf-8-sig") as f:
        if suffix == ".json":
            config = json.load(f)
        else:
            config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("配置最外层必须是对象，包含 tasks 字段。")

    tasks = config.get("tasks")

    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks 必须是非空列表。")

    required = {"name", "duration", "success_rate", "dependencies"}

    for index, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            raise ValueError(f"第 {index} 个任务必须是对象。")

        missing = required - task.keys()

        if missing:
            raise ValueError(
                f"第 {index} 个任务缺少字段：{', '.join(sorted(missing))}"
            )

    return config


def main():
    parser = argparse.ArgumentParser(
        description="TaskScheduler：任务调度模拟器"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="任务配置路径，支持 JSON、YAML",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError, RecursionError) as exc:
        print(f"错误：无法加载配置：{exc}", file=sys.stderr)
        return 1

    tasks = config["tasks"]

    print(f"成功读取 {len(tasks)} 个任务。")
    print(f"配置超时：{config.get('timeout', 15)} 秒（未填写时默认 15 秒）。")
    print("当前阶段：仅展示配置，尚未执行任务。")

    for task in tasks:
        print(
            f"{task['name']} | 时长={task['duration']}秒 | "
            f"成功率={task['success_rate']} | 依赖={task['dependencies']}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())