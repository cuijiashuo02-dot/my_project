#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import argparse
import json
import sys
from pathlib import Path
import random
import time

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

def validate_config(config):
    """检查字段取值、任务重名和依赖是否存在。"""
    timeout = config.get("timeout", 15)

    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout 必须是大于 0 的有限数字。")

    tasks = config["tasks"]
    names = set()

    # 第一遍：检查各任务字段，并收集全部任务名称。
    for index, task in enumerate(tasks, start=1):
        name = task["name"]

        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"第 {index} 个任务的 name 必须是非空字符串。")

        if name in names:
            raise ValueError(f"任务名重复：{name}")

        names.add(name)

        duration = task["duration"]

        if type(duration) not in (int, float) or not math.isfinite(duration) or duration < 0:
            raise ValueError(
                f"任务 {name} 的 duration 必须是大于或等于 0 的有限数字。"
            )

        rate = task["success_rate"]

        if type(rate) not in (int, float) or not math.isfinite(rate) or not 0 <= rate <= 1:
            raise ValueError(
                f"任务 {name} 的 success_rate 必须是 0 到 1 之间的有限数字。"
            )

        deps = task["dependencies"]

        if not isinstance(deps, list) or any(
            not isinstance(dep, str) or not dep.strip()
            for dep in deps
        ):
            raise ValueError(
                f"任务 {name} 的 dependencies 必须是任务名列表，允许空列表。"
            )

        if len(deps) != len(set(deps)):
            raise ValueError(
                f"任务 {name} 的 dependencies 中存在重复任务名。"
            )

    # 第二遍：全部名称收集完成后，检查依赖是否存在。
    for task in tasks:
        for dep in task["dependencies"]:
            if dep not in names:
                raise ValueError(
                    f"任务 {task['name']} 依赖不存在的任务：{dep}"
                )
def topological_sort(tasks):
    """反复安排依赖已排好的任务，返回拓扑顺序。"""
    ordered = []
    placed = set()
    pending = list(tasks)

    while pending:
        waiting = []

        for task in pending:
            if all(dep in placed for dep in task["dependencies"]):
                ordered.append(task)
                placed.add(task["name"])
            else:
                waiting.append(task)

        if len(waiting) == len(pending):
            blocked = ", ".join(task["name"] for task in waiting)
            raise ValueError(
                f"存在循环依赖，以下任务无法排序：{blocked}"
            )

        pending = waiting

    return ordered
class TaskScheduler:
    """执行已排序任务，支持重试、依赖跳过和全局超时。"""

    def __init__(self, tasks, seed=None, timeout=15.0):
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout 必须是大于 0 的有限数字。")

        self.tasks = tasks
        self.rng = random.Random(seed)
        self.timeout = float(timeout)
        self.results = {}
        self.total_duration = 0.0
        self.timed_out = False

    def log(self, status, name, message):
        colors = {
            "SUCCESS": "\033[32m",
            "FAILED": "\033[31m",
            "RETRY": "\033[33m",
            "SKIPPED": "\033[34m",
            "TIMEOUT": "\033[31m",
        }

        line = f"[{status}] {name}：{message}"

        if sys.stdout.isatty() and status in colors:
            line = f"{colors[status]}{line}\033[0m"

        print(line, flush=True)

    def wait_for_attempt(self, duration):
        """等待任务耗时，但不超过全局剩余时间。"""
        remaining = self.deadline - time.monotonic()

        if remaining <= 0:
            return False

        time.sleep(min(duration, remaining))

        return time.monotonic() < self.deadline

    def run(self, start_time=None):
        run_start = time.monotonic() if start_time is None else start_time
        self.deadline = run_start + self.timeout
        self.timed_out = False

        self.results = {
            task["name"]: {
                "name": task["name"],
                "status": "PENDING",
                "attempts": 0,
                "duration": 0.0,
                "started_at": None,
                "ended_at": None,
            }
            for task in self.tasks
        }

        for task in self.tasks:
            if time.monotonic() >= self.deadline:
                self.timed_out = True
                break

            name = task["name"]
            record = self.results[name]

            blocked = [
                dep
                for dep in task["dependencies"]
                if self.results[dep]["status"] != "SUCCESS"
            ]

            if blocked:
                record["status"] = "SKIPPED"
                self.log(
                    "SKIPPED",
                    name,
                    f"前置任务未成功：{', '.join(blocked)}",
                )
                continue

            record["started_at"] = time.time()
            task_start = time.monotonic()

            for attempt in range(1, 4):
                if time.monotonic() >= self.deadline:
                    self.timed_out = True
                    record["status"] = "TIMEOUT"
                    break

                record["attempts"] = attempt

                self.log(
                    "RUNNING",
                    name,
                    f"第 {attempt}/3 次尝试，预计 {task['duration']} 秒",
                )

                if not self.wait_for_attempt(task["duration"]):
                    self.timed_out = True
                    record["status"] = "TIMEOUT"
                    break

                if self.rng.random() < task["success_rate"]:
                    record["status"] = "SUCCESS"
                    self.log(
                        "SUCCESS",
                        name,
                        f"第 {attempt} 次尝试成功",
                    )
                    break

                self.log(
                    "FAILED",
                    name,
                    f"第 {attempt} 次尝试失败",
                )

                if attempt < 3:
                    self.log("RETRY", name, "准备再次尝试")
                else:
                    record["status"] = "FAILED"

            record["ended_at"] = time.time()
            record["duration"] = time.monotonic() - task_start

            if self.timed_out:
                break

        if time.monotonic() >= self.deadline:
            self.timed_out = True

        if self.timed_out:
            for record in self.results.values():
                if record["status"] == "PENDING":
                    record["status"] = "TIMEOUT"

            self.log(
                "TIMEOUT",
                "TaskScheduler",
                "达到全局时间限制，停止调度",
            )

        self.total_duration = time.monotonic() - run_start
        return self.results

    def build_report(self):
        return {
            "timeout": self.timed_out,
            "total_duration": self.total_duration,
            "tasks": list(self.results.values()),
        }
def write_report(report, report_path):
    """将报告保存为 JSON 文件。"""
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            report,
            f,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        f.write("\n")
def main():
    program_start = time.monotonic()

    parser = argparse.ArgumentParser(
        description="TaskScheduler：任务调度模拟器"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="任务配置路径，支持 JSON、YAML",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="全局超时秒数，覆盖配置中的 timeout",
    )
    parser.add_argument(
        "--report",
        default="report.json",
        help="报告路径，默认 report.json",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="随机种子，用于复现任务结果",
    )
    args = parser.parse_args()

    try:
        if Path(args.config).resolve() == Path(args.report).resolve():
            raise ValueError("报告路径不能与输入配置路径相同。")

        config = load_config(args.config)

        if args.timeout is not None:
            config["timeout"] = args.timeout

        validate_config(config)
        ordered_tasks = topological_sort(config["tasks"])

        runner = TaskScheduler(
            ordered_tasks,
            seed=args.seed,
            timeout=config.get("timeout", 15),
        )

        print(
            f"开始调度，全局时间限制：{runner.timeout} 秒。",
            flush=True,
        )

        results = runner.run(start_time=program_start)
        report = runner.build_report()
        write_report(report, args.report)

    except (
        OSError,
        UnicodeError,
        ValueError,
        OverflowError,
        yaml.YAMLError,
        RecursionError,
    ) as exc:
        print(f"错误：任务处理失败：{exc}", file=sys.stderr)
        return 1

    print("\n=== 最终结果 ===")

    for record in results.values():
        print(
            f"{record['name']} | "
            f"状态={record['status']} | "
            f"尝试={record['attempts']}次 | "
            f"耗时={record['duration']:.3f}秒"
        )

    print(f"总耗时：{runner.total_duration:.3f}秒")
    print(f"报告已保存：{args.report}")

    if runner.timed_out:
        return 124

    if all(record["status"] == "SUCCESS" for record in results.values()):
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())