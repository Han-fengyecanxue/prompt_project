# Prompt 抗数值幻觉对照评测报告

- 评测年份: 2023 | 报告期: 年报
- 模型: deepseek-v4-flash | temperature: 0.3
- 评测样本数: 8 | 调 LLM 次数: 24

## 逐样本结果

| 样本 | 公司 | 策略 | 引用准确率% | 备注 |
|---|---|---|---|---|
| S1 | 沪电股份 | baseline | 0.0 |  |
| S1 | 沪电股份 | injected | ERR | The read operation timed out |
| S1 | 沪电股份 | strict | 97.2 |  |
| S2 | 云南白药 | baseline | 8.7 |  |
| S2 | 云南白药 | injected | 91.4 |  |
| S2 | 云南白药 | strict | 98.7 |  |
| S3 | 泸州老窖 | baseline | 17.5 |  |
| S3 | 泸州老窖 | injected | 94.4 |  |
| S3 | 泸州老窖 | strict | 100.0 |  |
| S4 | 立讯精密 | baseline | ERR | The read operation timed out |
| S4 | 立讯精密 | injected | 87.4 |  |
| S4 | 立讯精密 | strict | 97.9 |  |
| S5 | 长春高新 | baseline | 5.0 |  |
| S5 | 长春高新 | injected | 92.7 |  |
| S5 | 长春高新 | strict | 97.9 |  |
| S6 | 古井贡酒 | baseline | 11.5 |  |
| S6 | 古井贡酒 | injected | 89.6 |  |
| S6 | 古井贡酒 | strict | 100.0 |  |
| S7 | 深南电路 | baseline | 6.2 |  |
| S7 | 深南电路 | injected | 88.4 |  |
| S7 | 深南电路 | strict | 100.0 |  |
| S8 | 智飞生物 | baseline | 0.0 |  |
| S8 | 智飞生物 | injected | 92.4 |  |
| S8 | 智飞生物 | strict | 98.3 |  |

## 汇总

| 策略 | 平均引用准确率% | 样本数 |
|---|---|---|
| baseline | 7.0 | 7 |
| injected | 90.9 | 7 |
| strict | 98.8 | 8 |
