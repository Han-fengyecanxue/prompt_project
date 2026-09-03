# 基于Prompt工程的上市公司财报解读与行业对标系统

省级大学生创新创业训练计划项目(淮阴师范学院 · 计算机科学与技术)

**架构**: Spring Boot 3.4 + MyBatis + MySQL 5.7 + Druid (后端) | Vue3 + ECharts (前端, 待开发)
**核心思想**: 双层解耦 —— 底层由系统精确计算财务指标与行业对标(可溯源、可验证), 上层通过"角色设定+数据注入+输出约束"三层 Prompt 驱动大模型生成自然语言解读报告(防幻觉)。

---

## 零、协作者上手指南(从 GitHub Clone 之后)

```bash
git clone https://github.com/Han-fengyecanxue/prompt_project.git
cd prompt_project
```

1. **初始化数据库**(二选一):
   - 一键脚本: `cd sql && init_db.bat`(按提示输入 MySQL 密码, 默认导入**真实财报数据**; 输入 S 可选模拟演示数据)
   - 手动: 先执行 `sql/01_schema.sql` 建表, 再执行 `sql/03_real_data.sql` 导入真实财报数据(3行业24家公司 2021-2025, 来源: 东方财富/新浪公开接口)
2. **配置本地环境**: 复制 `src/main/resources/config/application-development.properties.example` 为
   `application-development.properties`, 填入你自己的 MySQL 密码(该文件已被 .gitignore 忽略, 不会提交)
3. **启动后端**: `.\mvnw.cmd -DskipTests package && java -jar target\prompt_project-0.0.1-SNAPSHOT.jar`(端口 8091)
4. **计算指标与行业对标**(首次必做): `curl -X POST http://localhost:8091/api/finance/recalc -H "Content-Type: application/json" -d "{}"`
5. 浏览器访问 `http://localhost:8091/` 看到服务信息页即成功; 如需真实大模型, 在配置中填 `ai.api-key` 并把 `ai.provider` 改为 `openai`

> 默认数据为**真实财报数据**(东方财富/新浪公开接口采集, 采集脚本 `sql/fetch_real_data.py`); `sql/02_seed_data.sql` 为早期模拟演示数据(量级近似, 非真实), 仅供功能演示备选。

---

## 一、快速启动

### 1. 环境要求
- JDK 17+ (本项目已在 JDK 25 上验证)
- Maven (项目自带 `mvnw`, 无需全局安装)
- MySQL 5.7+ (本地 3306, 默认账号 root/13390797306, 可在配置中修改)

### 2. 初始化数据库
```bash
cd sql
# 建库建表(幂等, 会重建所有表)
mysql -uroot -p --default-character-set=utf8mb4 -e "source 01_schema.sql"
# 导入真实财报数据(东方财富/新浪采集, 24家x2021-2025, 已与公开年报核对)
mysql -uroot -p --default-character-set=utf8mb4 -e "source 03_real_data.sql"
# (可选)若要模拟演示数据: py -3 gen_seed.py && mysql -uroot -p --default-character-set=utf8mb4 -e "source 02_seed_data.sql"
```

### 3. 启动后端
```bash
# Windows
.\mvnw.cmd -DskipTests package
java -jar target\prompt_project-0.0.1-SNAPSHOT.jar
# 服务端口 8091
```

### 4. 计算指标与行业对标
```bash
curl -X POST http://localhost:8091/api/finance/recalc -H "Content-Type: application/json" -d "{}"
```
首次导入种子数据后必须执行一次重算(或数据变更后重新执行), 系统会自动:
1. 由原始数据计算 12 项标准化财务指标 → 写入 `财务指标`
2. 按 行业×年度×指标 计算均值/中位数/标准差/P25/P75 → 写入 `行业对标`

### 5. 配置大模型 (可选)
编辑 `src/main/resources/config/application-development.properties`:
```properties
# mock: 离线演示模式(无需Key, 由规则生成确定性报告)
# openai: 任意 OpenAI 兼容接口 (DeepSeek/通义千问/智谱/OpenAI 等)
ai.provider=openai
ai.base-url=https://api.deepseek.com/v1
ai.api-key=sk-xxxx
ai.model=deepseek-chat
```

---

## 二、数据库设计 (库名: 财报分析系统)

| 表名 | 说明 | 关键字段 |
|---|---|---|
| `行业分类` | 行业(证监会代码) | 行业ID, 行业代码, 行业名称 |
| `上市公司` | 公司基础信息 | 公司ID, 股票代码, 股票简称, 行业ID |
| `报表项目` | 财报科目字典(22项) | 项目编码(operating_revenue 等) |
| `财务原始数据` | 公司×年度×科目的金额(元) | 公司ID, 财年, 项目ID, 金额 |
| `财务指标` | 标准化指标(计算引擎产出) | 公司ID, 财年, 指标编码, 指标值, 单位 |
| `行业对标` | 行业统计基准 | 行业ID, 财年, 指标编码, 均值/中位数/标准差/P25/P75 |
| `提示词模板` | 三层Prompt模板 | 模板类型(角色设定/数据注入/输出约束) |
| `估值快照` | 收盘价/总市值(计算PE/PB) | 公司ID, 快照日期, 收盘价, 总市值 |
| `解读报告` | AI简报/对话记录(防幻觉审计) | 公司ID, 报告类型, AI回答, 上下文JSON |

### 指标体系 (12 项, 详见 `IndicatorDef`)

| 维度 | 指标 | 方向 |
|---|---|---|
| 盈利能力 | roe 净资产收益率 / gross_margin 毛利率 / net_margin_parent 归母净利率 | 越高越好 |
| 成长性 | revenue_growth 营收增长率 / profit_growth 归母净利润增长率 | 越高越好 |
| 财务风险 | asset_liability_ratio 资产负债率 / current_ratio 流动比率 / quick_ratio 速动比率 | 负债率越低越好, 比率越高越好 |
| 盈利质量 | cashflow_quality 经营现金流/净利润 | 越高越好 |
| 每股指标 | eps 基本每股收益 | 越高越好 |
| 估值 | pe 市盈率 / pb 市净率 | 越低越便宜 |

### 对标口径
- 行业样本: 同行业(行业ID)上市公司同一年度年报
- 统计量: 均值、中位数、P25、P75(线性插值)、总体标准差
- 百分位: `(严格小于该值的样本数)/(样本数-1)×100`; 方向调整后得到评分 score(0-100, 越高越优)
- 排名: higher_better 指标值最大为第 1 名; lower_better 指标值最小为第 1 名

---

## 三、接口设计表 (详见 `docs/接口设计表.md`)

### 财务模块 `/api/finance`
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/finance/industries` | 行业列表(含公司数) |
| GET | `/api/finance/companies` | 公司分页查询(keyword/industryId) |
| GET | `/api/finance/companies/{id}` | 公司详情 |
| GET | `/api/finance/profile` | 财务画像(原始数据+指标+估值) |
| GET | `/api/finance/trend` | 多年度指标趋势 |
| GET | `/api/finance/benchmark` | 行业对标(值/基准/百分位/排名) |
| GET | `/api/finance/ranking` | 行业指标排名 |
| POST | `/api/finance/screening` | 多条件交叉筛选(gt/lt/between/pct_gt/pct_lt) |
| POST | `/api/finance/recalc` | 重算指标与行业对标 |

### AI 模块 `/api/ai`
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/ai/templates` | 三层 Prompt 模板列表 |
| POST | `/api/ai/report` | 生成财报解读简报 |
| POST | `/api/ai/chat` | 上下文感知的追问对话 |
| GET | `/api/ai/reports` | 报告/对话记录(分页) |
| GET | `/api/ai/reports/{id}` | 报告详情 |

统一响应: `{"code":"0","message":"success","data":...}`, 业务错误码见 `ErrorCodeEnums`。

---

## 四、项目结构

```
src/main/java/com/fycx
├── prompt_project/PromptProjectApplication.java  启动类
├── common/       错误码/业务异常/全局异常/指标定义
├── config/       Druid数据源/CORS
├── controller/   财务 + AI 接口, request/response DTO
├── entity/       9 张表实体
├── mapper/       MyBatis Mapper 接口
├── service/
│   ├── calc/     指标计算引擎 + 行业对标统计引擎
│   └── impl/     FinanceServiceImpl / AiServiceImpl(三层Prompt+LLM客户端)
src/main/resources
├── mapper/*.xml  9 个 Mapper XML
└── config/application-development.properties
sql/              建表脚本 + 种子数据生成器
docs/             接口设计表
```

## 五、验证数据 (3 行业 24 家上市公司, 2021-2025)

- C39 计算机通信电子: 中际旭创/新易盛/天孚通信/立讯精密/工业富联/沪电股份/深南电路/生益科技
- C27 医药制造: 恒瑞医药/药明康德/迈瑞医疗/片仔癀/云南白药/复星医药/智飞生物/长春高新
- C15 酒饮料精制茶: 贵州茅台/五粮液/泸州老窖/山西汾酒/洋河股份/古井贡酒/今世缘/青岛啤酒

> 数据说明: 默认数据为**真实财报数据**——由 `sql/fetch_real_data.py` 从东方财富数据中心接口(三大报表)、新浪财经日K(年末收盘价)采集, 覆盖 3 行业 24 家上市公司 2021—2025 年报,
> 与公开年报核对无误(如贵州茅台 2023 营收 1476.94 亿元)。`sql/02_seed_data.sql` 为早期**模拟数据**(随机生成、量级近似), 仅作功能演示备选, 不再默认使用。
