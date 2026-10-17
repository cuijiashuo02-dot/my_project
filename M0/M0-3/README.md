# M0-3 传感器数据分析排查记录

## 程序目标

读取包含 time、value 两列的 CSV 文件，计算 value 的均值和标准差，
剔除与均值的绝对偏差超过两倍标准差的数据，
将保留的 time、value 写入 cleaned_data.csv。

## 问题 1：CSV 列名大小写不一致

- 定位：原始脚本第 37 行，`row["Value"]`。
- 现象：运行时报 `KeyError: 'Value'`。
- 原因：CSV 表头为小写 `value`，字典键区分大小写。
- 修复：将 `row["Value"]` 改为 `row["value"]`。
- 验证：重新运行后，原来的 KeyError 消失，程序能够读取 60 条数据。
- 后续问题：程序在输出阶段报告 `/out/cleaned_data.csv` 路径不存在，尚待修复。