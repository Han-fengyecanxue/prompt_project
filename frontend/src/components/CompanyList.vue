<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const emit = defineEmits(['select'])

const industries = ref([])
const list = ref([])
const total = ref(0)
const loading = ref(false)
const err = ref('')

const query = ref({ keyword: '', industryId: '', page: 1, size: 10 })

async function load() {
  loading.value = true
  err.value = ''
  try {
    const params = {
      keyword: query.value.keyword || undefined,
      industryId: query.value.industryId || undefined,
      page: query.value.page,
      size: query.value.size
    }
    const data = await api.companies(params)
    list.value = data.list
    total.value = data.total
  } catch (e) {
    err.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try { industries.value = await api.industries() } catch (e) { err.value = e.message }
  load()
})
</script>

<template>
  <div class="card">
    <div class="row">
      <input v-model="query.keyword" placeholder="输入股票代码 / 简称 / 全称" @keyup.enter="query.page = 1; load()" />
      <select v-model="query.industryId" @change="query.page = 1; load()">
        <option value="">全部行业</option>
        <option v-for="i in industries" :key="i.industryId" :value="i.industryId">
          {{ i.industryName }}({{ i.companyCount }}家)
        </option>
      </select>
      <button @click="query.page = 1; load()">查询</button>
      <span class="muted">共 {{ total }} 家</span>
    </div>

    <p v-if="err" class="err">{{ err }}</p>
    <p v-if="loading" class="muted mt">加载中…</p>

    <table v-if="list.length" class="mt">
      <thead>
        <tr><th>股票代码</th><th>股票简称</th><th>所属行业</th><th>交易所</th><th>上市日期</th></tr>
      </thead>
      <tbody>
        <tr v-for="c in list" :key="c.companyId" class="clickable" @click="emit('select', c)">
          <td>{{ c.stockCode }}</td>
          <td>{{ c.stockName }}</td>
          <td>{{ c.industryName }}</td>
          <td>{{ c.exchange }}</td>
          <td>{{ c.listDate }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading" class="muted mt">暂无数据</p>

    <div class="row mt" v-if="total > query.size">
      <button class="secondary" :disabled="query.page <= 1" @click="query.page--; load()">上一页</button>
      <span class="muted">第 {{ query.page }} 页</span>
      <button class="secondary" :disabled="query.page * query.size >= total" @click="query.page++; load()">下一页</button>
    </div>

    <p class="muted mt">💡 点击公司行进入「财务画像 · 行业对标」</p>
  </div>
</template>
