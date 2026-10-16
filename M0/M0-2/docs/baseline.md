#
# M0-2 原始程序运行记录

## 运行环境

- 日期：2026-10-16
- Python 环境：Conda 的 python310
- 运行目录：M0/M0-2/original
- 运行命令：python3 legacy_corr.py

## 遇到的问题

首次运行报错：
ModuleNotFoundError: No module named 'yaml'

原因：当前 Python 环境没有安装 YAML 解析库。

解决方法：
python3 -m pip install PyYAML

安装结果：Successfully installed PyYAML-6.0.3

## 再次运行结果

n = 40
mean_x = 49.43782499999999
mean_y = 43.310725
r = 0.00015648828136792707

## 初步发现

程序已经能够读取配置和数据。
相关系数计算的分母缺少平方根，下一步在工作版本中修正。