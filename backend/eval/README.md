# backend/eval — Prompt 抗数值幻觉对照实验

本目录是论文**实验章节**的全部可复现材料：评测脚本、逐条原始记录、合并统计与最终图表。

> 结论速览见 [`analysis_summary.md`](analysis_summary.md)；本文档说明**文件构成、口径与复现步骤**。

---

## 一、文件构成

### 证据（不可改写的实验记录）

| 文件 | 内容 |
|---|---|
| `eval_result_2024.raw.json` | 2024 年 6 家公司 × 6 策略 = **36** 条逐条记录 |
| `eval_result_2023.raw.json` | 2023 年 6 家公司 × 6 策略 = **36** 条 |
| `eval_result_2024.md` / `eval_result_2023.md` | 上述两次运行的自动生成报告（人读版） |

每条记录包含：`company / code / year / strategy / context_json`（注入的财务上下文）、
`answer`（模型原始回答）、`verified` / `unverified`（逐数字判定）、`acc`（严格口径）、
`acc_loose`（宽松口径）、`claims`，以及运行时原生记录的
`model / base_url / temperature / prompt_version / prompt_sha1 / llm_calls / elapsed_s /
prompt_tokens / completion_tokens / total_tokens / ts` —— 可直接支撑论文的"实验设置"与"成本与时延"。

### 脚本

| 脚本 | 用途 |
|---|---|
| `eval_report.py` | **跑评测**：拉取基准数据 → 组装 Prompt → 调模型 → 校验 → 写 md 与 raw.json |
| `report_validator.py`（在 `../tools/`） | 数值溯源校验器：判定报告中的数字能否在注入锚点中找到 |
| `merge_stats.py` | **合并两年记录 → 描述统计 + Wilcoxon 配对检验**，输出 `merged_stats.md` / `.json` |
| `backfill_meta.py` | 为早期 raw.json 补写复原元数据（幂等，已执行完毕） |

### 产物

| 文件 | 内容 |
|---|---|
| `analysis_summary.md` | **论文结果章节底稿**：描述统计、显著性检验、结论要点、修订记录 |
| `merged_stats.md` / `merged_stats.json` | `merge_stats.py` 的直接输出（数据以脚本为准，勿手改） |

> 早期用于单年度作图的 `analyze.py` 已删除，其功能由 `merge_stats.py`（统计）与
> `../tools/plot_hallucination.py`（论文插图）覆盖，避免同一条链路存在两套实现。

---

## 二、复现步骤

```bash
# 1) 合并统计(论文表格直接取自这里)
py -3 backend/eval/merge_stats.py --markdown backend/eval/merged_stats.md --json backend/eval/merged_stats.json

# 2) 旧口径对照(用于说明 p 值差异来源, 非论文数据)
py -3 backend/eval/merge_stats.py --legacy-positional

# 3) 重跑评测(需后端 :8091 与 API Key)
#    --timeout 放宽到 180s 很重要: 默认 60s 会让推理型模型的长回答超时丢样本
py -3 backend/eval/eval_report.py --year 2024 --max-samples 6 --save-raw --timeout 180 --out eval_result_2024.md
py -3 backend/eval/eval_report.py --year 2023 --max-samples 6 --save-raw --timeout 180 --out eval_result_2023.md
```

不传 `--companies` 时脚本按"行业轮流抽取"自动选样本；由于公司列表按 `stock_code` 排序，
会稳定选中沪电股份/云南白药/泸州老窖/立讯精密/长春高新/古井贡酒这 6 家，保证跨轮次可比。

**必须使用装有 scipy 的解释器**（本项目验证于 `py -3`，Python 3.14 + scipy 1.17）；
`plot_hallucination.py` 需要 matplotlib。`merge_stats.py` 在没有 scipy 时会回退为正态近似，
n=12 的精确 p 值会失真（例如 0.0005 会算成 0.0022），论文数值请以装 scipy 的环境复算为准。

---

## 三、统计口径

- **配对方式**：按 `(year, companyId)` **匹配配对**。这是配对符号秩检验的前提。
  早期临时脚本按列表位置 `zip` 配对，在样本缺失时会造成 12 对中 9 对错配，已修正；
  当前数据两年各 36 条、无缺失，两种口径结果一致。`--legacy-positional` 可复现旧口径以便对照。
- **严格口径 `acc`**：报告中所有数字能在注入锚点集合内溯源的比例（含年份等叙述性整数，最严）。
- **宽松口径 `acc_loose`**：剔除叙述性整数后，指向财务指标数值的溯源比例。
- **未溯源数字数**：`len(unverified)`，即单份报告中的疑似幻觉数字个数，越低越好。
- **显著性**：Wilcoxon 符号秩检验，α=0.05；平均增益 = 后一策略 − 前一策略。

---

## 四、已知局限（论文须一并披露）

1. **样本量小**：n=12（2 年 × 6 家公司），每个行业仅 2 家，属小样本案例研究，**不可外推为行业规律**。
2. **单一模型**：全部实测仅 `deepseek-v4-flash`（接口回显名 `deepseek-flash`）一个模型，
   本地模型（qwen3.5:2b / deepseek-r1:7b）因内存不足只跑了 1~3 条冒烟，因此本实验是
   **单一模型上的 Prompt 消融**，不含跨模型对比；这些无统计意义的冒烟记录已从仓库移除。
3. **输出不可逐轮复现**：temperature=0.3 下同一输入的输出仍有随机性，重跑会得到不同的逐样本数值；
   可比较的是策略间的相对关系与结论方向。逐条模型名、温度、耗时、token 与 Prompt 指纹
   （`prompt_sha1`）均为**运行时原生记录**，可完整复核单次生成。
4. **校验器是规则筛查**：`report_validator.py` 只做候选数字筛查，不能替代年报核对；
   年份、位次等叙述性整数会进入严格口径，因此严格口径偏保守。
   `analysis_summary.md` 同时给出严格与宽松两套口径以便对照。
