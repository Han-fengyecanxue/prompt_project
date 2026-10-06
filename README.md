# 上市公司财报解读与行业对标系统 · 项目总目录

> 省级大学生创新创业训练计划项目
> 基于 **Prompt 工程**:底层系统精确计算财务指标与行业对标,上层三层 Prompt(角色设定/数据注入/输出约束)驱动大模型生成解读报告,防幻觉、可审计。

## 📁 目录结构

```
prompt_project/
├── backend/                  # 后端: Spring Boot 3.4 + MyBatis + MySQL(仓库 prompt_project.git)
│   ├── sql/                  #   建库脚本 01_schema.sql / 真实数据 03_real_data.sql / init_db.bat / 采集脚本
│   ├── src/                  #   Java 源码(controller/service/mapper/entity)
│   ├── tools/                #   Python 工具(报告数值校验 / 图表生成 / md2docx 转换)
│   ├── docs/                 #   文档(.md 为源 · .docx 由 tools/md2docx.py 生成) + 图表
│   ├── eval/                 #   论文对照实验: 评测脚本 + 逐条原始记录 + 统计脚本 + 结论(README.md)
│   ├── tests/                #   Python 质量测试
│   └── README.md             #   后端详细说明(克隆、初始化、启动、接口)
├── frontend/                 # 前端: Vue3 + Vite + ECharts(独立仓库 front.git)
│   ├── src/views/            #   六大页面: 系统概览/公司查询/财务画像/AI解读/行业排行/智能筛选
│   ├── src/components/       #   外壳(侧边导航/顶栏/公司选择器/通知) + 通用组件(图表/KPI卡/空状态/骨架屏)
│   ├── src/utils/            #   格式化 · 安全 Markdown 渲染 + 数值溯源校验 · ECharts 主题
│   ├── src/styles/           #   设计令牌 + 通用组件样式(无 UI 组件库依赖)
│   └── README.md             #   前端结构与功能说明
├── 启动后端.bat              # 双击启动后端(:8091)
├── 启动前端.bat              # 双击启动前端(:5173)
├── 参考资料_….docx           # 论文正文（服务省级期刊投稿，见下方说明）
├── 软件著作权申请材料/       # 软著登记材料：源程序文档 / 软件说明书 / 申请表信息与填表要点
├── 答辩材料/                 # 结题答辩：答辩PPT（含逐页讲稿备注）/ 讲稿与预期问答
└── README.md                 # 本文件
```

> 说明: 根目录的 `~$` 开头文件是 Word 打开时的临时锁文件, 关闭 Word 后可删除。
>
> `参考资料_*.docx` 为项目论文正文，用于**省级期刊投稿**；文件名沿用早期"参考资料"的叫法，
> 内容随实验数据更新（最新一次为 2026-10）。论文与软著材料均属申报材料，公开仓库中是否保留请按投稿要求自行判断。

## 🚀 快速启动(双击两个脚本即可)

前置:MySQL57 服务已运行(本机已建库 `financial_analysis`,含 24 家真实上市公司 2021–2025 年报数据)。

1. **双击 `启动后端.bat`** → 等出现端口 8091 监听(首次会自动 Maven 打包,约 1 分钟)
2. **双击 `启动前端.bat`** → 自动打开 http://localhost:5173
3. 从零初始化数据库(可选): `backend\sql\init_db.bat`,并在后端启动后执行一次指标重算:
   `curl -X POST http://localhost:8091/api/finance/recalc -H "Content-Type: application/json" -d "{}"`

## 📚 文档导航

| 文档 | 位置 | 内容 |
|---|---|---|
| 后端技术文档 | `backend/docs/技术文档.md` | 架构、数据库、**指标口径(含 ROE/PB 分母)**、验证状态与已知局限 |
| 接口设计表 | `backend/docs/接口设计表.md` | 全部 REST 接口入参/出参 |
| **Prompt 与模型上手指南** | `backend/docs/上手指南_Prompt与模型.md` | Prompt 工程 / 云端 API(DeepSeek 等) / 本地模型(Ollama) / 排错速查 |
| 深化研究方案 | `backend/docs/Prompt工程深化研究与系统扩展方案.md` | 研究问题、数据核验、Prompt 对照实验设计、评价指标 |
| **实验与论文数据** | `backend/eval/README.md` · `analysis_summary.md` | 评测脚本、逐条记录、描述统计与 Wilcoxon 检验、已知局限 |
| 后端 README | `backend/README.md` | 协作者克隆/构建/启动指南 |
| **前端说明** | `frontend/README.md` | 前端目录结构、页面功能、设计说明与常见问题 |
| **软著申请材料** | `软件著作权申请材料/` | 源程序文档（60 页）/ 软件说明书（18 页）/ 申请表信息与填表要点 |
| **答辩材料** | `答辩材料/` | 答辩 PPT（15 页，每页含讲稿备注）与讲稿、17 条预期问答、演示兜底方案 |

> 📄 文档约定: `*.md` 为**唯一源文件**; `*.docx` 由 `backend/tools/md2docx.py` 从同名 `.md` 生成, 属**派生产物**, 请勿直接编辑。文档索引见 `backend/docs/README.md`。

## 🔑 关键配置速查

- **数据库**: `financial_analysis`(9 张英文表: industry_category / listed_company / report_item / financial_raw_data / financial_indicator / industry_benchmark / prompt_template / valuation_snapshot / ai_report)
- **AI 供应商** `backend/src/main/resources/config/application-development.properties`:
  `ai.provider=mock`(默认离线) → 改 `openai` + 填 `ai.api-key` 即接云端(DeepSeek/通义);`ai.base-url=http://localhost:11434/v1` 即接本地 Ollama
- **端口**: 后端 8091 · 前端 5173(前端 /api 代理到 8091)
