# M0-2 CSV 两列相关系数分析工具

## 功能

读取 YAML 配置及 CSV 数据，手写计算两列数值的 Pearson 相关系数。
支持命令行指定配置、输入检查和清晰的错误提示。
NumPy 只用于测试比对，不参与业务计算。

## 环境与依赖

使用 Python 3.10 或更高版本，在已创建的 Conda 环境中运行。

```bash
conda activate python310
cd /home/frank/Projects/my_project/M0/M0-2
python3 -m pip install -r requirements.txt
```

## 运行方法

在本题目录运行：

```bash
python3 corr.py --config config.yaml
```

省略 --config 时，默认读取当前工作目录下的 config.yaml。

在仓库根目录运行：

```bash
python3 M0/M0-2/corr.py --config M0/M0-2/config.yaml
```

查看帮助：

```bash
python3 corr.py --help
```

## 配置格式

```yaml
input_csv: "sample_data.csv"
columns:
  x: "sensor_a"
  y: "sensor_b"
task:
  name: "corr_analysis"
  verbose: true
```

input_csv 和 columns.x、columns.y 为必填项。
CSV 相对路径以配置文件所在目录为基准。
task 可省略；verbose 默认 true，设为 false 时只打印 r。
task.name 为任务标签，不参与计算。

## CSV 要求

使用 UTF-8 编码，允许 UTF-8 BOM，第一行为表头。
列名精确匹配并区分大小写，允许存在其他列。
至少包含两对有效数值，选定列不能包含空值、非数值、NaN 或无穷大。
任意一列不能全部相同，否则相关系数无定义。
程序不自动删除离群值，也不把错误数据替换为零。

## 输出说明

随附样例有 40 对数据，结果约为：

```text
n = 40
mean_x = 49.437825
mean_y = 43.310725
r = 0.563474725452
```

n 为数据对数量，mean_x、mean_y 为两列均值。
r 为 Pearson 相关系数，取值范围为 [-1, 1]。
接近 1/-1 表示较强的正/负线性关系。
接近 0 表示线性相关较弱，不能据此判断不存在其他关系。
相关性不代表因果关系。

## 异常处理

文件不存在、配置错误、空文件、缺列、非法数值及零方差等情况，
在 stderr 输出可读错误信息，并以非零退出码结束。
正常结果输出至 stdout，成功退出码为 0。

```bash
python3 corr.py --config no_such_config.yaml
echo $?
```

## 自动测试

从 M0/M0-2 目录执行：

```bash
python3 -m unittest discover -s tests -v
```

包含 12 个测试方法，覆盖已知结果、NumPy 比对、
异常输入、跨目录运行、输出控制和导入保护。
本机实际运行结果保存在 docs/test_result.txt。

## 过程材料

original/：保留原始代码与数据。
checks/：人工异常输入样例。
docs/baseline.md：首次运行、依赖报错及处理记录。
tests/：自动测试。
requirements.txt：依赖清单。

原始公式的分母缺少平方根，已修正。
当前使用去均值、偏差缩放和 math.fsum 改善数值计算。
超出浮点数表示能力的数据仍需先调整量级。