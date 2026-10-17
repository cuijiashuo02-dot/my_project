# M0-4 TaskScheduler

## 项目目标

实现命令行任务调度模拟器，支持配置加载、依赖排序、
随机执行、失败重试、依赖跳过、全局超时、彩色日志和 JSON 报告。

## 当前进度

已实现配置加载阶段：

- 支持 JSON、YAML、YML 文件。
- 使用 --config 指定配置路径，该参数必填。
- 保留完整配置，包括 timeout 和 tasks。
- 检查配置基本结构与任务必要字段。
- 对读取和解析错误给出可读提示及非零退出码。

后续实现字段校验、拓扑排序及任务执行功能。

## 环境与依赖

使用 Python 虚拟环境。

安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

## 本阶段运行方式

```bash
python3 scheduler.py --config tasks_demo.json
```

```bash
python3 scheduler.py --config tasks_demo.yaml
```

查看帮助：

```bash
python3 scheduler.py --help
```

## 验证记录

- 官方 JSON 配置读取出 7 个任务。
- 官方 YAML 配置读取出相同的 7 个任务。
- 正常读取退出码为 0。
- 文件不存在时提示原因，退出码为 1，未出现 Traceback。