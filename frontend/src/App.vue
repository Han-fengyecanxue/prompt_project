<script setup>
import { ref } from 'vue'
import CompanyList from './components/CompanyList.vue'
import ProfileView from './components/ProfileView.vue'
import AiView from './components/AiView.vue'
import RankingView from './components/RankingView.vue'
import ScreeningView from './components/ScreeningView.vue'

const tab = ref('list')          // list | profile | ai | ranking | screening
const selected = ref(null)       // 选中的公司

function selectCompany(c) {
  selected.value = c
  tab.value = 'profile'
}
</script>

<template>
  <div class="shell">
    <header>
      <h1>📊 上市公司财报解读与行业对标系统</h1>
      <span class="sub">基于 Prompt 工程 · Spring Boot 3.4 + Vue3 + ECharts</span>
    </header>

    <nav>
      <button :class="{ active: tab === 'list' }" @click="tab = 'list'">公司查询</button>
      <button :class="{ active: tab === 'profile' }" @click="tab = 'profile'">财务画像 · 行业对标</button>
      <button :class="{ active: tab === 'ai' }" @click="tab = 'ai'">AI 解读</button>
      <button :class="{ active: tab === 'ranking' }" @click="tab = 'ranking'">行业排行</button>
      <button :class="{ active: tab === 'screening' }" @click="tab = 'screening'">智能筛选</button>
    </nav>

    <main>
      <CompanyList v-show="tab === 'list'" @select="selectCompany" />
      <!-- 图表页用 v-if: 避免在隐藏状态初始化图表导致宽度为 0 -->
      <ProfileView v-if="tab === 'profile'" :company="selected" @select="selectCompany" />
      <RankingView v-if="tab === 'ranking'" @select="selectCompany" />
      <ScreeningView v-if="tab === 'screening'" @select="selectCompany" />
      <!-- 对话页用 v-show: 保留聊天记录 -->
      <AiView v-show="tab === 'ai'" :company="selected" />
    </main>

    <footer class="muted">数据来源: 东方财富 / 新浪公开财报接口(2021–2025 年报, 24 家上市公司 × 3 行业) · 系统仅用于学习研究, 不构成投资建议</footer>
  </div>
</template>

<style scoped>
.shell { max-width: 1180px; margin: 0 auto; padding: 20px 16px 40px; }
header { display: flex; align-items: baseline; gap: 14px; margin-bottom: 14px; }
header h1 { font-size: 22px; color: #1f3b63; }
header .sub { color: #888; font-size: 13px; }
nav { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
nav button { background: #e4e9f2; color: #444; }
nav button.active { background: #1f3b63; color: #fff; }
main { min-height: 60vh; }
footer { margin-top: 30px; text-align: center; }
</style>
