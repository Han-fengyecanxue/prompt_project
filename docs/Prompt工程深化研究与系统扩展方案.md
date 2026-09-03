# Prompt工程深化研究与系统扩展方案

> 版本: v1.0 | 日期: 2026-09-03 | 配套系统: prompt_project（Spring Boot 3.4 + Vue3）
> 本文目的: 在现有"三层Prompt + 数据锚定"实现之上，系统梳理 Prompt 工程的研究纵深与工程扩展点，
> 为论文第4章/5.4节深化、以及"接入真实大模型API调用"提供可执行路线。

---

## 一、现状盘点（已实现）

| 能力 | 落点 | 说明 |
|------|------|------|
| 三层Prompt模板 | `提示词模板`表(角色设定/数据注入/输出约束) + `AiServiceImpl` | DB存储、带版本号与启用标记，可在线切换 |
| 数据锚定 | `buildDataJson()` → system层注入 | 指标+对标结果JSON是"唯一可信数据来源"，明文声明 |
| 负面指令约束 | `输出约束`模板第1/6条 | 禁编造、缺失显式声明"无法分析" |
| 确定性降级 | `mockGenerate()` | provider=mock 或 API 失败时降级，数字仍全部来自注入数据 |
| 多轮追问 | `chat()` + history | 沿用同一注入上下文，关键词/别名/维度匹配 |
| 留痕审计 | `解读报告`表(上下文字段) | 每份报告保存注入JSON，支持"报告↔数据"复算 |
| 温度控制 | temperature=0.3 | 低随机性 |
| 兼容接口 | `callOpenAICompatible()` | 任意 OpenAI 兼容 chat/completions（DeepSeek/通义/智谱/Kimi…），配置即切 |

**已有研究产出**：`docs/report_validator.py`（数值幻觉自动校验器，原型）——提取报告全部数字与注入JSON锚点比对。
实测库中茅台2023简报(ID=1)：回答数字53个，可溯源53个，**数值引用准确率100%，疑似幻觉0**。
该校验器把"抗幻觉"从口号变成了可自动计算的指标，是后续所有Prompt对照实验的评分基础。

## 二、抑制幻觉的方法谱系与研究纵深

幻觉按成因分三类：**记忆幻觉**（模型凭训练记忆作答）、**推理幻觉**（计算/逻辑错误）、**忠实度幻觉**（偏离给定上下文）。
通用缓解分三层：训练层（RLHF/指令微调）、推理层（解码约束）、**应用层（检索/锚定/提示设计/输出校验）**——本系统属应用层路线，
已做"数据锚定+负面指令"，可继续深化的应用层技术：

1. **少样本示例（Few-shot）**：在输出约束后附加1~2条"注入数据→合格报告"的范例，稳定格式与引用习惯。
   注意：财报场景范例必须用**脱敏或历史真实数据**写死，防止模型模仿范例里的数字。
2. **"先复述、后分析"的两段式提示（数字复述步）**：要求模型第一步仅把关键指标"数值+对标位置"复述成清单，
   第二步再写分析。复述清单是纯机械任务，便于程序校验，把幻觉拦截在成文之前（比直接CoT更适合数值任务——
   财报分析中的"链式推理"若自由发挥反而易编造中间数）。
3. **结构化中间输出（JSON mode）**：让模型先输出 `{维度, 结论, 引用值, 对标表述, 评级}` 的结构化JSON，
   程序校验通过后再渲染为自然语言报告。校验失败→自动重试或降级。多数兼容API已支持 response_format=json。
4. **输出校验器（Validator，后处理）**：生成后自动检查——报告中的每个数字都必须在注入JSON中可检索
   （本系统已实现原型，见上）。校验不通过时可触发"修正提示"（把可疑数字列表回传模型要求改写）或直接拦截。
   这是**投入产出比最高**的扩展，且完全离线、与模型无关。
5. **引用溯源（Grounded Citation）**：报告数字旁标注数据卡片锚点（如 `ROE 34.87% ⟶ 指标卡#roe`），前端悬浮显示
   该指标在行业中的位置。让"数据锚定"在用户体验层可见、可点击、可复核。
6. **自一致性（Self-consistency）**：同一请求采样N次（如3次，temperature稍高），对结论/评级做多数投票，
   数值取众数或交集。成本×N，适合对"综合评级"这类高风险结论做稳健化。
7. **动态模板与行业知识注入**：按行业注入口径说明（如银行业需调整存贷比等特殊科目口径；本系统当前为制造业/酒饮，
   口径较统一）；按报告维度缺失情况自动裁剪章节（已在输出约束第6条预留）。
8. **评测驱动迭代（Eval-driven）**：构建固定评测集（如24家×5年×12指标的数字复述任务），每次改模板跑全量评测，
   用准确率/幻觉数/结构合规率决定是否上线——配套模板表"版本号"做A/B与回滚。DSPy等框架将这一流程自动化，
   可在后续引入为实验脚手架，但生产链路保持轻量。
9. **多模型横向对比**：同一Prompt在不同模型（DeepSeek/通义/智谱/Kimi/豆包，均OpenAI兼容）上跑评测集，
   选择性价比最优者；也可研究"强模型解读、轻模型复述"的分工。
10. **RAG扩展（年报文本）**：将巨潮PDF年报（管理层讨论MD&A、审计意见、附注）切片向量化，检索后与数值共同注入，
    实现"数值+文本"融合解读——属于P2，需要embedding与向量库。

## 三、系统可扩展点清单（按优先级）

### P0 —— 建议近期实现（不动架构，收益立现）

| # | 扩展点 | 说明 | 涉及模块 | 工作量 |
|---|--------|------|----------|--------|
| A | 真实LLM API激活与加固 | 填key即用(已支持openai模式)；建议补：请求级超时/重试/429退避、max_tokens、调用日志(tokens/耗时/费用) | AiServiceImpl、解读报告表加列 | 0.5~1d |
| B | 生成后数值校验钩子 | 把report_validator逻辑用Java实现(或调用)，生成后自动校验并把"数值引用准确率/可疑数"写入报告记录；可疑数>0且非mock时触发一次修正重试 | AiServiceImpl、AiReport实体 | 1~2d |
| C | 评测集+批量评测脚本 | 固定(公司,财年)抽样集，自动生成→自动校验→输出对比表(模板版本×模型×指标) | docs/eval_*.py（Python，复用validator） | 1d |
| D | Prompt版本A/B标记 | 请求参数带templateVersion，报告落库，便于按版本聚合统计效果 | 请求体+报告表 | 0.5d |

### P1 —— 增强解读质量

| # | 扩展点 | 说明 |
|---|--------|------|
| E | 两段式/JSON中间输出 | 先结构化中间结果并校验，再渲染成文（可作"开关"对比研究） |
| F | Few-shot范例模板 | 输出约束后附1条标准范例（数字用历史报告真实值） |
| G | 追问推荐与上下文管理 | 简报页提供"可追问问题"引导；对话超长时压缩历史 |
| H | 引用溯源UI | Markdown数字→数据卡悬浮；报告可一键"复核数据" |
| I | 行业口径说明注入 | 模板数据注入层附加行业字典(如行业名称/样本构成/特殊口径) |

### P2 —— 中长期/论文展望

| # | 扩展点 | 说明 |
|---|--------|------|
| J | 年报文本RAG | MD&A/审计意见/附注检索注入，数值+文本融合解读 |
| K | 多模型对比与自一致性投票 | 评测驱动选型；综合评级多次采样投票 |
| L | 异步批量生成与财报季任务 | 队列化批量刷新报告，Docker编排 |
| M | LLM-as-judge报告质量分 | 与数值校验互补的语义质量评估（可读性/结构/评级合理性） |

## 四、API 调用扩展专题

### 4.1 现状

`AiServiceImpl.callOpenAICompatible()` 已完整实现 OpenAI 兼容的 chat/completions 调用：
`ai.provider=mock|openai`、`ai.base-url`（以 /v1 结尾）、`ai.api-key`、`ai.model`（默认 deepseek-chat）、
`ai.temperature`（默认0.3）、`ai.timeout-seconds`（默认60）。system=角色设定+数据注入，user=输出约束+指令，
支持多轮history；**调用失败自动降级mock**，系统永不白屏。

### 4.2 启用步骤（以 DeepSeek 为例）

1. 在 platform.deepseek.com 获取 API Key（充值按量计费）；
2. 修改 `src/main/resources/config/application-development.properties`：
   ```
   ai.provider=openai
   ai.base-url=https://api.deepseek.com/v1
   ai.api-key=sk-xxxx
   ai.model=deepseek-chat
   ai.temperature=0.3
   ```
3. 重启后端，前端"生成简报"即走真实模型；API故障自动回退mock。
4. 验证：`py -3 docs/report_validator.py --all` 观察真实模型报告的数值引用准确率（预期对比mock是否下降、下降多少）。

成本粗估（deepseek-chat 2026年价格量级）：一次简报输入≈2~3k tokens、输出≈1k tokens，单价以官方为准，
千次生成约数元级别；评测集全量(24×5=120次×3组模板)约1~2元量级，成本可控。

### 4.3 建议增强

- **流式输出（SSE）**：前端打字机效果，长报告首字延迟从~10s降到<1s；后端需改SSE透传（Java HttpClient 不支持流式，
  建议换 WebClient/OkHttp 或直接转发）。
- **重试与退避**：5xx重试2次指数退避；429读Retry-After；超时分级（首token/总时长）。
- **max_tokens与惩罚**：上限设1200；frequency_penalty=0 避免数字表述被改写。
- **计费与日志**：记录每次调用 prompt/response tokens、耗时、模型、模板版本→解读报告表或独立日志表。
- **合规**：提示词与数据本地组装、仅请求时出网；报告落库附"不构成投资建议"声明（已在mock模板中）；
  敏感数据不外传（本项目为公开财报数据，风险低）。

### 4.4 多模型对比（横向评测）

同一评测集换 base-url/model 即可跑通义千问(qwen-plus)/智谱(glm-4)/Kimi(moonshot-v1)/豆包(doubao)等，
产出"模型×模板"效果矩阵，是论文"实验"章节的天然素材。

## 五、对照实验设计（升级版，供论文§5.4使用）

评测集：24家×5年×12指标中抽样（如每行业2家×2年=12个任务），任务=复述性解读。
评分器：`report_validator.py`（数值引用准确率/可疑幻觉数，全自动、零人工、可复现）+ 人工抽检语义。

| 组 | Prompt配置 | 研究问题 |
|----|-----------|----------|
| A | 仅角色设定（无数据注入） | 基线：模型凭记忆作答的幻觉率 |
| B | 角色+数据注入（无负面指令/结构约束） | 数据锚定单独的作用 |
| C | 完整三层模板（系统默认） | 锚定+约束叠加的效果 |
| C+FS | C + 少样本范例 | Few-shot增量 |
| C+RP | C + "先复述后分析"两段式 | 复述步对幻觉的拦截 |
| C+JS | C + JSON中间输出+程序校验 | 结构化中间层的效果 |
| C+V | C + 生成后校验器（可疑数字回传改写） | 后处理兜底效果 |

指标：①数值引用准确率 ②可疑幻觉数 ③结构合规率 ④评级与规则评级一致率 ⑤(真实模型)单次成本与延迟。
预期结论（待实测）：A组幻觉率高；B组显著下降但格式失控；C组起格式与引用稳定；
C+RP/C+JS/C+V 为"准确保真"再加保险；mock模式恒为100%（确定性），作为全实验的上界参照。

## 六、研究路线建议（配合大创进度 2026.10—2027.1 "不同提示词对模型影响"阶段）

1. **第1~2周**：落地 P0-A/B/C（真实API + Java校验钩子 + Python评测脚本）；
2. **第3~4周**：实现 E/F（两段式、Few-shot），跑 C vs C+FS vs C+RP 评测；
3. **第5~8周**：接入 2~3 家国产模型做横向对比，产出效果矩阵与成本报告；
4. 结题前：把评测数据、校验器结果、模板版本演进写进论文实验章节与结题报告。

## 七、与论文的衔接

本文档的"五、实验设计"可直接升级论文§5.4；"二、方法谱系"可充实论文§1.2/§4的Related Work与方案论述；
校验器100%实测数据可作为论文"抗幻觉可量化验证"的初步证据；P0/P1清单可写入"后续工作"。
需要时可将本方案要点合并回论文正文（我来改）。

## 参考文献（扩展阅读，均为公开真实文献）

1. Wei J, et al. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. arXiv:2201.11903, 2022.
2. Wang X, et al. Self-Consistency Improves Chain of Thought Reasoning in Language Models. arXiv:2203.11171, 2022.
3. Yao S, et al. ReAct: Synergizing Reasoning and Acting in Language Models. arXiv:2210.03629, 2022.
4. Ouyang L, et al. Training language models to follow instructions with human feedback. NeurIPS 2022.
5. Lewis P, et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. arXiv:2005.11401, 2020.
6. Khattab O, et al. DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines. arXiv:2310.03714, 2023.
7. Zheng L, et al. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. arXiv:2306.05685, 2023.
8. OpenAI. API Reference: JSON mode / Structured Outputs. https://platform.openai.com/docs
9. DeepSeek. API 文档. https://api-docs.deepseek.com
