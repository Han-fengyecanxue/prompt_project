# 前端 · 上市公司财报解读与行业对标系统

> 大学生创新创业训练计划项目 · 前端仓库
> 技术栈：**Vue 3.5**(`<script setup>`) + **Vite 6** + **ECharts 6**（按需引入，无 UI 组件库依赖）

---

## 一、快速启动

```bash
npm install          # 首次
npm run dev          # 开发模式 -> http://localhost:5173 (/api 代理到 8091)
```

也可以打包后以静态方式预览（**答辩现场更稳**，不启动文件监听）：

```bash
npm run build        # 产物输出到 dist/
npm run preview      # 静态预览 -> http://localhost:5173 (同样代理 /api 到 8091)
```

> 后端未启动时前端不会白屏：顶栏会显示「后端未连接」，各页面给出可重试的错误提示。

---

## 二、目录结构

```
frontend/
├─ index.html                  首屏骨架 + SEO/图标
├─ vite.config.js              代理 / 分包 / base 配置
└─ src/
   ├─ main.js                  应用入口
   ├─ App.vue                  外壳：侧边导航 + 顶栏 + Hash 路由
   ├─ api.js                   后端接口封装（统一解包 CommonResponse + 超时 + 错误分类）
   ├─ store.js                 全局状态（字典/健康状态/当前公司/财年/通知）
   ├─ styles/
   │   ├─ tokens.css           设计令牌（颜色/间距/圆角/阴影/字体）
   │   └─ base.css             基础样式 + 通用组件类（卡片/按钮/表格/标签/骨架屏…）
   ├─ utils/
   │   ├─ format.js            数字/金额/百分比/日期格式化、CSV 导出、剪贴板
   │   ├─ markdown.js          安全 Markdown 渲染 + **数值溯源校验**
   │   ├─ charts.js            ECharts 按需注册 + `fin` 主题 + 公共 option 片段
   │   └─ nav.js               导航元数据（单一数据源）
   ├─ components/              AppSidebar / AppTopbar / CompanyPicker / EChart / StatCard /
   │                           EmptyState / SkeletonTable / ToastHost /
   │                           IndicatorTip(指标释义气泡) / AppDrawer(侧滑抽屉)
   └─ views/                   Dashboard / CompanyList / Profile / Ai / Ranking / Screening
```

---

## 三、页面与功能

| 页面 | 路由 | 主要能力 |
|---|---|---|
| 系统概览 | `#/dashboard` | 项目定位、数据规模 KPI、行业分布、指标维度覆盖、核心流程、运行状态 |
| 公司查询 | `#/list` | 关键字 + 行业检索、表格/卡片双视图、分页、点击进入画像 |
| 财务画像 | `#/profile/:companyId` | 综合评分环、关键指标卡、**六维能力雷达**、指标趋势、行业对标图与可排序明细表、指标速览、报表科目 |
| AI 解读 | `#/ai/:companyId` | 三层 Prompt 模板展示、分步生成提示、**数值溯源高亮**、追问对话、历史记录 |
| 行业排行 | `#/ranking` | 行业 + 指标筛选、Top3 领奖台、分布统计、横向分布图、明细表、导出 CSV |
| 智能筛选 | `#/screening` | 多条件 AND 编辑、4 组预设方案、条件判定明细、导出 CSV |

### 几个值得说明的设计点

1. **数值溯源高亮（防幻觉的可视化）**
   `utils/markdown.js` 会把 AI 报告里的每个数字与「财务画像 / 行业对标」的计算结果比对：
   能匹配到的标 **绿色**，未匹配到的标 **黄色**，并在报告顶部给出「数值可溯源率」。
   这与后端 `ai_report.numeric_accuracy` 字段互为印证，是"双层解耦"思想在前端的落点。
   统计时会自动排除年份、章节序号、`P75`/`C39` 这类标识符中的数字与 6 位股票代码，避免误报。

2. **Hash 路由**：`#/profile/17` 这样的链接可刷新、可直接分享，答辩演示时不必再点一遍。

3. **图表自适应**：`EChart.vue` 用 `ResizeObserver` 跟随容器尺寸（含侧边栏折叠、栅格变化），
   并在卸载时 `dispose()`，避免内存泄漏。

4. **按需引入 ECharts**：只注册用到的图表与组件，打包体积比全量引入显著减小。

5. **导出与打印**：对标明细、趋势、排行、筛选结果均可导出 **带 BOM 的 CSV**（Excel 打开中文不乱码）；
   画像页与 AI 报告支持浏览器打印 / 存 PDF，便于直接放进结题材料。

6. **无 UI 组件库**：所有组件自建，依赖只有 `vue` 与 `echarts`，`npm install` 快、体积小、可控。

---

## 四、后端接口约定

前端统一通过 `/api` 相对路径访问（由 Vite 代理到 `http://localhost:8091`）。
后端统一响应体 `{ code, message, data }`，`code === '0'` 才视为成功，`api.js` 已统一解包。

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/health` | 顶栏运行状态 |
| GET | `/api/finance/industries` | 行业字典（含公司数） |
| GET | `/api/finance/indicators` | 指标元数据（编码/名称/维度/单位/方向） |
| GET | `/api/finance/companies` | 公司分页检索 |
| GET | `/api/finance/companies/{id}` | 公司详情（深链还原用） |
| GET | `/api/finance/profile` | 财务画像 |
| GET | `/api/finance/benchmark` | 行业对标（含百分位/评分/排名） |
| GET | `/api/finance/trend` | 多年度指标趋势 |
| GET | `/api/finance/ranking` | 行业指标排名 |
| POST | `/api/finance/screening` | 多条件交叉筛选 |
| GET | `/api/ai/templates` | 三层 Prompt 模板 |
| POST | `/api/ai/report` | 生成解读简报 |
| POST | `/api/ai/chat` | 追问对话 |
| GET | `/api/ai/reports` | 历史报告 / 对话记录 |

完整入参出参见 `backend/docs/接口设计表.md`。

---

## 五、常见问题

**Q：页面显示「无法连接后端服务」？**
A：先启动后端（项目根目录「启动后端.bat」，端口 8091），再刷新页面；顶栏的红色状态徽标可以直接点击重新检测。

**Q：图表是空白的？**
A：图表数据依赖指标重算结果。首次导入数据库后需执行一次
`curl -X POST http://localhost:8091/api/finance/recalc -H "Content-Type: application/json" -d "{}"`。

**Q：`npm run dev` 报 `EBUSY: resource busy or locked, watch ...`？**
A：这是编辑器写文件时留下的临时目录被 Vite 监听到导致的，`vite.config.js` 已忽略 `**/*.tmpdir/**`；
若仍出现，删除 `src` 下的 `.xxx.tmpdir` 目录后重启即可，或改用 `npm run build && npm run preview`。
