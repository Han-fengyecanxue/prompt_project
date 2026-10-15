<script setup>
/**
 * 统一图标出口: 用语义 name 映射 lucide 线性图标, 颜色继承 currentColor, 便于全局换风格
 */
import { computed } from 'vue'
import {
  LayoutDashboard, Search, Target, Lightbulb, Trophy, ListFilter,
  Building2, Factory, ChartColumn, TrendingUp, Medal, Crown,
  SearchX, Inbox, TriangleAlert, Sparkles, Table2,
  Database, Calculator, ListOrdered, RefreshCw, Ruler, CalendarDays, Hash, Zap,
  Radar, ScrollText, Printer, FileText,
  MessageSquare
} from 'lucide-vue-next'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 16 },
  stroke: { type: Number, default: 2 }
})

const MAP = {
  overview: LayoutDashboard,   // 系统概览
  search: Search,              // 公司查询 / 检索
  searchx: SearchX,            // 未找到
  target: Target,              // 财务画像 / 对标
  ai: Sparkles,                // AI 解读
  notice: Lightbulb,           // 提示说明
  ranking: Trophy,             // 行业排行
  screening: ListFilter,       // 智能筛选
  company: Building2,          // 样本公司
  industry: Factory,           // 覆盖行业
  chart: ChartColumn,          // 行业分布
  trend: TrendingUp,           // 指标趋势
  medal1: Medal,               // 排行榜 1
  medal2: Crown,               // 排行榜 2
  medal3: Medal,               // 排行榜 3
  empty: Inbox,                // 空状态
  warn: TriangleAlert,         // 错误 / 警告
  table: Table2,               // 溯源表格
  database: Database,          // 数据采集
  calculator: Calculator,      // 指标计算
  rank: ListOrdered,           // 行业对标/排行
  sync: RefreshCw,             // 流程闭环
  ruler: Ruler,                // 指标维度
  calendar: CalendarDays,      // 财年/年度
  number: Hash,                // 数据点
  zap: Zap,                    // 快捷体验
  radar: Radar,                // 能力雷达
  relist: ScrollText,          // 指标速览
  print: Printer,              // 打印
  report: FileText,            // 报表科目
  chat: MessageSquare          // 追问对话
}

const icon = computed(() => MAP[props.name] || LayoutDashboard)
</script>

<template>
  <component :is="icon" :size="Number(size)" :stroke-width="stroke" aria-hidden="true" />
</template>