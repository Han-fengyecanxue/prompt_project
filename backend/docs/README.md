# backend/docs 文档索引

本目录存放项目**文档**与**论文图表**; 可执行工具在 [`../tools/`](../tools/)。

> **约定**: `*.md` 为**唯一源文件**; `*.docx` 由 `../tools/md2docx.py` 从同名 `.md` 生成, 属**派生产物**。
> 修改内容请改 `.md`, 再重新生成 `.docx`, 不要直接编辑 `.docx`。

## 文档

| 文件 | 内容 |
|---|---|
| [技术文档.md](技术文档.md) · 技术文档.docx | 后端架构、数据库、接口、计算引擎说明 |
| [接口设计表.md](接口设计表.md) · 接口设计表.docx | 全部 REST 接口入参/出参 |
| [上手指南_Prompt与模型.md](上手指南_Prompt与模型.md) | Prompt 工程 / 云端 API(DeepSeek) / 本地模型(Ollama) / 文生图提示词 |
| [Prompt工程深化研究与系统扩展方案.md](Prompt工程深化研究与系统扩展方案.md) | 幻觉校验、实验设计与扩展点 |

## 图表

- `figures/fig1_accuracy.png` · `fig2_hallucinations.png` · `fig3_compliance.png`
- 由 [`../tools/plot_hallucination.py`](../tools/plot_hallucination.py) 依据本目录 `eval_data.csv` 生成
- `eval_data.csv` 当前为**示意数据**(非论文实测结果), 接入真实大模型后回填

> 可执行工具见 [`../tools/`](../tools/); 评测脚本与结果见 [`../eval/`](../eval/)。
