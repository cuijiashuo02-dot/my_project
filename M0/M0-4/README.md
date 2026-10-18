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
## 当前进度

已实现：

- JSON、YAML、YML 配置读取。
- 基本结构和必要字段检查。
- 超时、耗时和成功率的数值校验。
- 任务名非空与唯一性检查。
- 依赖列表格式、重复依赖和不存在的依赖检查。
- 拓扑排序，支持分叉与汇合。
- 循环依赖检测。

当前只规划任务顺序，下一步实现执行、重试和依赖跳过。

## 排序方法

反复扫描待安排任务，将所有前置任务都已排好位置的任务
加入结果。暂时不能安排的任务留到下一轮。

如果一整轮没有安排任何任务，则报告循环依赖。
排序只规划顺序，不代表任务已经执行成功。
## 第二阶段验证

- 官方 JSON、YAML 配置均通过校验和排序。
- 颠倒配置中的任务顺序后，仍满足全部依赖关系。
- 不存在的依赖、循环依赖、成功率越界均被识别。
## 执行与重试规则

- 任务按拓扑顺序逐个执行。
- 所有前置任务必须为 SUCCESS，当前任务才会执行。
- 每次尝试等待 duration 秒，再随机判断结果。
- 最多尝试 3 次，首次成功后停止重试。
- 三次全部失败，最终状态为 FAILED。
- 前置任务未成功时，当前任务为 SKIPPED，尝试次数为 0。
- 跳过继续向下游传播，独立分支继续执行。
- 任务耗时包含全部尝试和重试。
- 全部任务成功时退出码为 0，否则为 1。

## 随机种子

```bash
python3 scheduler.py --config tasks_demo.json --seed 42
```

同样的配置、执行顺序和种子可以复现状态与尝试次数，
实际耗时和时间戳不要求完全一致。

## 执行逻辑测试

```bash
python3 -m unittest discover -s tests -p test_execution.py -v
```

覆盖失败传播、独立任务继续执行、第三次成功和种子复现。
## 参数

| 参数 | 说明 |
|---|---|
| --config | 必填，支持 .json、.yaml、.yml |
| --timeout | 可选，覆盖配置中的超时时间 |
| --report | 可选，默认 report.json |
| --seed | 可选，指定随机种子 |

超时优先级：命令行参数、配置字段、默认 15 秒。

## 三个运行示例

### 正常成功

```bash
python3 scheduler.py --config tasks_demo.yaml --timeout 15 --report report.json --seed 7
```

### 观察失败、重试和依赖跳过

```bash
python3 scheduler.py --config tasks_demo.json --timeout 15 --report docs/failure_report.json --seed 42
```

### 验证全局超时

```bash
python3 scheduler.py --config tasks_demo.json --timeout 1 --report docs/timeout_report.json --seed 42
```

## 超时与报告约定

- 所有任务和重试共用一个全局截止时间。
- 等待时间不超过剩余预算，等待后再次检查超时。
- 超时中断当前任务，并停止启动后续任务。
- 已完成任务保留最终结果，剩余未处理任务记为 TIMEOUT。
- 报告包含配置中的每个任务。
- 未开始任务的 attempts 为 0、duration 为 0，时间戳为 null。
- 任务 duration 包括该任务的全部尝试。
- total_duration 从主函数开始计时到调度结束。
- 终端日志使用颜色，重定向到文件时输出普通文字。

## 退出码

- 0：全部成功。
- 1：任务未全部成功，或配置、文件处理错误。
- 124：全局超时。

## 测试

```bash
python3 -m unittest discover -s tests -v
```
## 完成情况

已实现配置加载与校验、拓扑排序、循环依赖检测、
随机执行、最多三次尝试、依赖跳过、全局超时、
终端彩色日志和 JSON 报告。

程序采用顺序执行方式，支持依赖关系中的分叉和汇合。
分叉表示多个任务可能具备执行条件，不表示并行运行。
## 最终验证

在 Conda 虚拟环境中完成验证，环境信息见：

- docs/environment.txt

完整测试命令：

```bash
python3 -m unittest discover -s tests -v
```

测试记录见：

- docs/final_test_result.txt

验证覆盖三种配置扩展名、依赖排序、错误配置、
失败重试、下游跳过、独立任务继续执行、种子复现、
超时等待截断、报告结构和非终端日志输出。

## 设计选择

- 使用独立随机数生成器，便于固定种子重复调试。
- 使用单调时钟计算耗时，使用真实时间戳记录开始和结束时间。
- 所有任务和重试共享一个全局截止时间。
- 先建立全部任务记录，确保跳过和超时任务不会从报告中遗漏。
- 使用反复扫描的拓扑排序，便于理解，适合本题的小规模任务。