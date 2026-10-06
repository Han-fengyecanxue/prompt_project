# backend/docs 文档索引

本目录存放项目**文档**与**论文图表**; 可执行工具在 [`../tools/`](../tools/),
评测脚本与实验记录在 [`../eval/`](../eval/)。

> **约定**: `*.md` 为**唯一源文件**; `*.docx` 由 [`../tools/md2docx.py`](../tools/md2docx.py)
> 从同名 `.md` 生成, 属**派生产物**。修改内容请改 `.md`, 再重新生成 `.docx`, 不要直接编辑 `.docx`。

## 文档

| 文件 | 内容 |
|---|---|
| [技术文档.md](技术文档.md) · 技术文档.docx | 后端架构、数据库、计算口径、验证状态与已知数据局限 |
| [接口设计表.md](接口设计表.md) · 接口设计表.docx | 全部 REST 接口入参/出参 |
| [上手指南_Prompt与模型.md](上手指南_Prompt与模型.md) | Prompt 工程 / 云端 API(DeepSeek) / 本地模型(Ollama) / 排错速查 |
| [Prompt工程深化研究与系统扩展方案.md](Prompt工程深化研究与系统扩展方案.md) | 研究问题、数据核验、Prompt 对照实验设计、评价指标与执行清单 |

## 论文图表

| 文件 | 内容 |
|---|---|
| `figures/fig1_accuracy.png` | 不同 Prompt 配置下报告数值引用准确率对比 |
| `figures/fig2_hallucinations.png` | 不同 Prompt 配置下疑似幻觉数字数对比(越低越好) |

- **数据来源**: 真实实测。`figures/` 由 [`../tools/plot_hallucination.py`](../tools/plot_hallucination.py)
  读取 [eval_data.csv](eval_data.csv) 生成; 该 CSV 已回填 2023+2024 两年合并 **(n=12)** 的实测结果,
  与 [`../eval/analysis_summary.md`](../eval/analysis_summary.md) 一致。
- **重新生成**: `py -3 tools/plot_hallucination.py`(需 matplotlib; 中文字体用 Windows 黑体)。
- **只画实测组**: 脚本默认排除 `source != 实测` 的行。系统 `mock` 模式是确定性功能测试,
  **不是大模型实验组**, 不得出现在论文插图中(需要查看时用 `--include-nonreal`)。
- 图表与统计的完整口径、样本构成、局限说明见 [`../eval/README.md`](../eval/README.md)。

> 早期版本曾使用示意数据, 并计划生成 `fig3_compliance.png`; 该图**未实现也未使用**,
> 结构合规率的评估方法见[深化研究方案](Prompt工程深化研究与系统扩展方案.md), 尚未产出实测数据。
