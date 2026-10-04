# Prompt 抗数值幻觉对照评测报告

- 评测年份: 2024 | 报告期: 年报
- 模型: deepseek-v4-flash | temperature: 0.3
- 评测样本数: 3 | 调 LLM 次数: 9

## 逐样本结果

| 样本 | 公司 | 策略 | 引用准确率% | 备注 |
|---|---|---|---|---|
| S1 | 沪电股份 | baseline | 33.3 |  |
| S1 | 沪电股份 | injected | 89.7 |  |
| S1 | 沪电股份 | strict | 100.0 |  |
| S2 | 云南白药 | baseline | 11.1 |  |
| S2 | 云南白药 | injected | 85.1 |  |
| S2 | 云南白药 | strict | 98.8 |  |
| S3 | 长春高新 | baseline | 7.9 |  |
| S3 | 长春高新 | injected | 87.9 |  |
| S3 | 长春高新 | strict | 96.3 |  |

## 汇总

| 策略 | 平均引用准确率% | 样本数 |
|---|---|---|
| baseline | 17.4 | 3 |
| injected | 87.6 | 3 |
| strict | 98.4 | 3 |
