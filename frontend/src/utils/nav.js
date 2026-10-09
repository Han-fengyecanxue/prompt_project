/** 视图导航元数据(侧边栏 / 顶栏共用, 单一数据源) */
export const NAV = [
  { key: 'dashboard', icon: '📊', label: '系统概览', desc: '项目与数据总览', hint: '项目定位 · 数据规模 · 指标维度 · 运行状态' },
  { key: 'list',      icon: '🔍', label: '公司查询', desc: '检索上市公司', hint: '按代码 / 简称 / 行业检索 24 家样本公司' },
  { key: 'profile',   icon: '🎯', label: '财务画像', desc: '指标 · 行业对标', hint: '指标趋势 · 行业分位 · 对标明细 · 报表科目' },
  { key: 'ai',        icon: '💡', label: 'AI 解读',  desc: 'Prompt 生成报告', hint: '三层 Prompt · 数据注入 · 数值溯源校验' },
  { key: 'ranking',   icon: '🏆', label: '行业排行', desc: '指标横向排名', hint: '同行业同年度按指标横向排名' },
  { key: 'screening', icon: '🧮', label: '智能筛选', desc: '多条件交叉选股', hint: '多条件 AND 交叉筛选 · 条件判定明细' }
]

export const navMeta = (key) => NAV.find(n => n.key === key) || NAV[0]
