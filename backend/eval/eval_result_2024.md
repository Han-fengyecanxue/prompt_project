# Prompt 抗数值幻觉对照评测报告

- 评测年份: 2024 | 报告期: 年报
- 模型: deepseek-v4-flash | temperature: 0.3
- 评测样本数: 8 | 调 LLM 次数: 24

## 逐样本结果

| 样本 | 公司 | 策略 | 引用准确率% | 备注 |
|---|---|---|---|---|
| S1 | 沪电股份 | baseline | 15.2 |  |
| S1 | 沪电股份 | injected | 91.7 |  |
| S1 | 沪电股份 | strict | 96.9 |  |
| S2 | 云南白药 | baseline | 10.7 |  |
| S2 | 云南白药 | injected | 93.5 |  |
| S2 | 云南白药 | strict | 100.0 |  |
| S3 | 泸州老窖 | baseline | 0.0 |  |
| S3 | 泸州老窖 | injected | 91.4 |  |
| S3 | 泸州老窖 | strict | ERR | The read operation timed out |
| S4 | 立讯精密 | baseline | 17.6 |  |
| S4 | 立讯精密 | injected | 90.2 |  |
| S4 | 立讯精密 | strict | 97.7 |  |
| S5 | 长春高新 | baseline | 0.0 |  |
| S5 | 长春高新 | injected | 96.7 |  |
| S5 | 长春高新 | strict | ERR | The read operation timed out |
| S6 | 古井贡酒 | baseline | 14.3 |  |
| S6 | 古井贡酒 | injected | 89.9 |  |
| S6 | 古井贡酒 | strict | 99.0 |  |
| S7 | 深南电路 | baseline | 5.9 |  |
| S7 | 深南电路 | injected | 86.6 |  |
| S7 | 深南电路 | strict | 100.0 |  |
| S8 | 智飞生物 | baseline | 0.0 |  |
| S8 | 智飞生物 | injected | 88.2 |  |
| S8 | 智飞生物 | strict | 99.0 |  |

## 汇总

| 策略 | 平均引用准确率% | 样本数 |
|---|---|---|
| baseline | 8.0 | 8 |
| injected | 91.0 | 8 |
| strict | 98.8 | 6 |
