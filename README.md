# 上市公司财报解读与行业对标系统 · 项目总目录

> 省级大学生创新创业训练计划项目
> 基于 **Prompt 工程**:底层系统精确计算财务指标与行业对标,上层三层 Prompt(角色设定/数据注入/输出约束)驱动大模型生成解读报告,防幻觉、可审计。

## 📁 目录结构

```
prompt_project/
├── backend/                  # 后端: Spring Boot 3.4 + MyBatis + MySQL(仓库 prompt_project.git)
│   ├── sql/                  #   建库脚本 01_schema.sql / 真实数据 03_real_data.sql / init_db.bat / 采集脚本
│   ├── docs/                 #   技术文档.md · 接口设计表.md · 上手指南_Prompt与模型.md · 幻觉校验工具
│   ├── src/                  #   Java 源码(controller/service/mapper/entity)
│   └── README.md             #   后端详细说明(克隆、初始化、启动、API)
├── frontend/                 # 前端: Vue3 + Vite + ECharts(独立仓库 front.git, 原 Desktop\vuetest)
│   └── src/components/       #   公司查询/财务画像(图表)/AI解读/行业排行/智能筛选
├── scripts/                  # 辅助脚本(hosts-fix-github.cmd 等)
├── 启动后端.bat              # 双击启动后端(:8091)
├── 启动前端.bat              # 双击启动前端(:5173)
└── README.md                 # 本文件
```

> 说明: `论文示例_….docx` 为申报书/论文参考材料(保留在根目录);`~$` 开头是 Word 打开时的临时锁文件,关闭 Word 后可删除。

## 🚀 快速启动(双击两个脚本即可)

前置:MySQL57 服务已运行(本机已建库 `financial_analysis`,含 24 家真实上市公司 2021–2025 年报数据)。

1. **双击 `启动后端.bat`** → 等出现端口 8091 监听(首次会自动 Maven 打包,约 1 分钟)
2. **双击 `启动前端.bat`** → 自动打开 http://localhost:5173
3. 从零初始化数据库(可选): `backend\sql\init_db.bat`,并在后端启动后执行一次指标重算:
   `curl -X POST http://localhost:8091/api/finance/recalc -H "Content-Type: application/json" -d "{}"`

## 📚 文档导航

| 文档 | 位置 | 内容 |
|---|---|---|
| 后端技术文档 | `backend/docs/技术文档.md` | 架构、数据库、接口、计算引擎说明 |
| 接口设计表 | `backend/docs/接口设计表.md` | 全部 REST 接口入参/出参 |
| **Prompt 与模型上手指南** | `backend/docs/上手指南_Prompt与模型.md` | Prompt 工程 / 云端 API(DeepSeek 等) / 本地模型(Ollama) / 文生图提示词 |
| 深化研究方案 | `backend/docs/Prompt工程深化研究与系统扩展方案.md` | 幻觉校验、实验设计与扩展点 |
| 后端 README | `backend/README.md` | 协作者克隆/构建/启动指南 |

## 🔑 关键配置速查

- **数据库**: `financial_analysis`(9 张英文表: industry_category / listed_company / report_item / financial_raw_data / financial_indicator / industry_benchmark / prompt_template / valuation_snapshot / ai_report)
- **AI 供应商** `backend/src/main/resources/config/application-development.properties`:
  `ai.provider=mock`(默认离线) → 改 `openai` + 填 `ai.api-key` 即接云端(DeepSeek/通义);`ai.base-url=http://localhost:11434/v1` 即接本地 Ollama
- **端口**: 后端 8091 · 前端 5173(前端 /api 代理到 8091)
