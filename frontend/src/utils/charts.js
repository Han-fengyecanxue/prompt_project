/**
 * ECharts 统一封装
 * 1) 按需引入 —— 只注册本项目实际用到的图表与组件(直角坐标系/提示框/图例/标题/图形/雷达),
 *    相比 `import * as echarts from 'echarts'` 可显著减小打包体积
 * 2) 注册 'fin' 主题 —— 全站图表风格一致(字号/网格/配色/提示框)
 * 3) 导出共用的 option 片段与配色, 避免各页面重复配置
 */
import * as echarts from 'echarts/core'
import { LineChart, BarChart, PieChart, RadarChart, ScatterChart, GaugeChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  GraphicComponent, RadarComponent
} from 'echarts/components'
import { LabelLayout, UniversalTransition } from 'echarts/features'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  LineChart, BarChart, PieChart, RadarChart, ScatterChart, GaugeChart,
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  GraphicComponent, RadarComponent,
  LabelLayout, UniversalTransition, CanvasRenderer
])

export const PALETTE = ['#1d5288', '#2f6fd0', '#21b083', '#e2a134', '#7b58d6', '#3aa6b9', '#d9605c', '#93a3b8']

const AXIS_LINE = { lineStyle: { color: '#e1e8f0' } }
const AXIS_LABEL = { color: '#8a97a8', fontSize: 11 }
const SPLIT_LINE = { lineStyle: { color: '#eef2f7', type: 'dashed' } }

const THEME = {
  color: PALETTE,
  backgroundColor: 'transparent',
  textStyle: { fontFamily: "'Microsoft YaHei','PingFang SC',sans-serif", fontSize: 12, color: '#52637a' },
  title: { textStyle: { color: '#12305a', fontSize: 13, fontWeight: 600 }, subtextStyle: { color: '#8a97a8' } },
  legend: { textStyle: { color: '#52637a', fontSize: 11.5 }, itemWidth: 12, itemHeight: 8, itemGap: 14, icon: 'roundRect' },
  tooltip: {
    backgroundColor: 'rgba(255,255,255,.97)',
    borderColor: '#d3dde8',
    borderWidth: 1,
    padding: [8, 12],
    textStyle: { color: '#1b2733', fontSize: 12 },
    extraCssText: 'box-shadow:0 8px 24px rgba(16,35,61,.14);border-radius:8px;',
    axisPointer: {
      lineStyle: { color: '#b9c7da', type: 'dashed' },
      crossStyle: { color: '#b9c7da' },
      shadowStyle: { color: 'rgba(47,111,208,.07)' }
    }
  },
  grid: { left: 12, right: 16, top: 44, bottom: 8, containLabel: true },
  categoryAxis: {
    axisLine: AXIS_LINE, axisTick: { show: false }, axisLabel: AXIS_LABEL,
    splitLine: { show: false }
  },
  valueAxis: {
    axisLine: { show: false }, axisTick: { show: false }, axisLabel: AXIS_LABEL,
    splitLine: SPLIT_LINE, nameTextStyle: { color: '#8a97a8', fontSize: 11 }
  },
  line: { smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2 } },
  bar: { itemStyle: { borderRadius: [4, 4, 0, 0] } },
  pie: { itemStyle: { borderColor: '#fff', borderWidth: 2 }, label: { color: '#52637a', fontSize: 11.5 } },
  radar: { axisName: { color: '#52637a', fontSize: 11.5 } }
}

echarts.registerTheme('fin', THEME)

export { echarts }

/** 让图表容器在没有数据时展示统一占位 */
export const emptyOption = (text = '暂无数据') => ({
  graphic: {
    type: 'text', left: 'center', top: 'middle',
    style: { text, fill: '#a9b5c4', fontSize: 13, fontFamily: "'Microsoft YaHei',sans-serif" }
  },
  xAxis: { show: false }, yAxis: { show: false }, series: []
})

/** 数值轴: 统一缩放与网格 */
export const valueAxis = (extra = {}) => ({
  type: 'value', scale: true, splitLine: SPLIT_LINE, axisLabel: AXIS_LABEL, ...extra
})

/** 类目轴 */
export const categoryAxis = (data, extra = {}) => ({
  type: 'category', data, axisLine: AXIS_LINE, axisTick: { show: false }, axisLabel: AXIS_LABEL, ...extra
})

/** 提示框: 统一主题 */
export const tooltip = (extra = {}) => ({ ...THEME.tooltip, ...extra })

/** 图例 */
export const legend = (extra = {}) => ({ top: 8, ...THEME.legend, ...extra })

export default echarts
