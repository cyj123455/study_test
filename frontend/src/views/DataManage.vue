<template>
  <div class="page">
    <h1 class="page-title">数据管理</h1>

    <div class="card">
      <h2 class="card-title">加载本地数据（已配置路径）</h2>
      <p class="card-desc">从配置的 Excel 路径读取白菜、土豆价格与广州天气数据，预处理（缺失值填充、异常值剔除）后写入数据库。</p>
      <div class="form-row">
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="loadClearBefore" />
            加载前清空现有价格与天气数据
          </label>
        </div>
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="loadRemoveOutliers" />
            剔除价格异常值（均值±3倍标准差）
          </label>
        </div>
        <button class="btn btn-primary" :disabled="loadingLocal" @click="loadLocalData">
          {{ loadingLocal ? '加载中…' : '加载本地数据' }}
        </button>
      </div>
      <p v-if="loadLocalResult" class="result">{{ loadLocalResult }}</p>
    </div>

    <div class="card">
      <h2 class="card-title">Excel 导入</h2>
      <div class="form-row">
        <div class="form-group">
          <label>价格数据</label>
          <input type="file" accept=".xlsx,.xls" @change="onPriceFile" />
        </div>
        <button class="btn btn-primary" :disabled="uploading" @click="uploadPrice">上传价格</button>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>天气数据</label>
          <input type="file" accept=".xlsx,.xls" @change="onWeatherFile" />
        </div>
        <button class="btn btn-primary" :disabled="uploading" @click="uploadWeather">上传天气</button>
      </div>
      <p v-if="importResult" class="result">{{ importResult }}</p>
    </div>

    <div class="card">
      <h2 class="card-title">数据导出</h2>
      <div class="form-row flex-wrap">
        <div class="form-group">
          <label>数据类型</label>
          <select v-model="exportType">
            <option value="price">价格</option>
            <option value="weather">天气</option>
            <option value="integrated">集成数据</option>
          </select>
        </div>
        <div class="form-group">
          <label>开始日期</label>
          <input v-model="exportStart" type="date" />
        </div>
        <div class="form-group">
          <label>结束日期</label>
          <input v-model="exportEnd" type="date" />
        </div>
        <div class="form-group">
          <label>产品（可选，逗号分隔）</label>
          <input v-model="exportProducts" type="text" placeholder="本地白菜,土豆" />
        </div>
        <a :href="exportLink" class="btn btn-secondary" download>导出 Excel</a>
      </div>
    </div>

    <div class="card">
      <h2 class="card-title">价格数据列表</h2>
      <div class="form-row">
        <div class="form-group">
          <label>产品</label>
          <select v-model="queryProduct">
            <option value="">全部</option>
            <option value="矮脚白菜">矮脚白菜</option>
            <option value="本地白菜">本地白菜</option>
            <option value="小塘白菜">小塘白菜</option>
            <option value="土豆">土豆</option>
          </select>
        </div>
        <div class="form-group">
          <label>开始日期</label>
          <input v-model="queryStart" type="date" />
        </div>
        <div class="form-group">
          <label>结束日期</label>
          <input v-model="queryEnd" type="date" />
        </div>
        <button class="btn btn-primary" @click="loadPrices">查询</button>
      </div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>市场名称</th>
              <th>产品</th>
              <th>价格（元/公斤）</th>
              <th>地区</th>
              <th>日期</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in priceList" :key="r.id">
              <td>{{ r.market_name || '—' }}</td>
              <td>{{ r.product_name }}</td>
              <td>{{ r.price }}</td>
              <td>{{ r.origin || '—' }}</td>
              <td>{{ r.record_date }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="priceList.length === 0 && !loading" class="muted">暂无数据</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { data as dataApi } from '@/api'

const priceFile = ref<File | null>(null)
const weatherFile = ref<File | null>(null)
const uploading = ref(false)
const importResult = ref('')
const exportType = ref('price')
const exportStart = ref('')
const exportEnd = ref('')
const exportProducts = ref('')
const queryProduct = ref('')
const queryStart = ref('')
const queryEnd = ref('')
const priceList = ref<any[]>([])
const loading = ref(false)
const loadClearBefore = ref(true)
const loadRemoveOutliers = ref(true)
const loadingLocal = ref(false)
const loadLocalResult = ref('')

function onPriceFile(e: Event) {
  const t = (e.target as HTMLInputElement)
  if (t.files?.[0]) priceFile.value = t.files[0]
}
function onWeatherFile(e: Event) {
  const t = (e.target as HTMLInputElement)
  if (t.files?.[0]) weatherFile.value = t.files[0]
}

async function loadLocalData() {
  loadingLocal.value = true
  loadLocalResult.value = ''
  try {
    const res = await dataApi.loadLocal({
      clear_before: loadClearBefore.value,
      remove_outliers: loadRemoveOutliers.value,
    })
    const d = (res.data as any)
    loadLocalResult.value = `${d.message || '加载完成'}：价格 ${d.price_rows ?? 0} 条，天气 ${d.weather_rows ?? 0} 条`
    await loadPrices()
  } catch (e: any) {
    loadLocalResult.value = e.response?.data?.detail || '加载失败'
  } finally {
    loadingLocal.value = false
  }
}

async function uploadPrice() {
  if (!priceFile.value) return
  uploading.value = true
  importResult.value = ''
  try {
    const res = await dataApi.importPrice(priceFile.value)
    importResult.value = `成功导入 ${(res.data as any).imported ?? 0} 条价格数据`
  } catch (e: any) {
    importResult.value = e.response?.data?.detail || '上传失败'
  } finally {
    uploading.value = false
  }
}

async function uploadWeather() {
  if (!weatherFile.value) return
  uploading.value = true
  importResult.value = ''
  try {
    const res = await dataApi.importWeather(weatherFile.value)
    importResult.value = `成功导入 ${(res.data as any).imported ?? 0} 条天气数据`
  } catch (e: any) {
    importResult.value = e.response?.data?.detail || '上传失败'
  } finally {
    uploading.value = false
  }
}

const exportLink = computed(() => {
  const base = import.meta.env.VITE_API_BASE || ''
  const token = localStorage.getItem('token')
  const params = new URLSearchParams({ data_type: exportType.value })
  if (exportStart.value) params.set('date_start', exportStart.value)
  if (exportEnd.value) params.set('date_end', exportEnd.value)
  if (exportProducts.value) params.set('product_names', exportProducts.value)
  let url = `${base}/api/data/export?${params}`
  if (token) url += `&token=${token}`
  return url
})

async function loadPrices() {
  loading.value = true
  try {
    const res = await dataApi.listPrices({
      product_name: queryProduct.value || undefined,
      date_start: queryStart.value || undefined,
      date_end: queryEnd.value || undefined,
      page_size: 200,
    })
    priceList.value = res.data || []
  } catch {
    priceList.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadPrices)
</script>

<style scoped>
.form-row {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-row.flex-wrap {
  flex-wrap: wrap;
}

.form-row .form-group {
  margin-bottom: 0;
}

.form-row .form-group input[type="file"] {
  max-width: 260px;
}

.result {
  color: var(--accent);
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.table-wrap {
  overflow-x: auto;
  margin-top: 1rem;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.data-table th,
.data-table td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.data-table th {
  font-weight: 600;
  color: var(--text-muted);
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.card-desc {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: normal;
}

.checkbox-label input {
  width: auto;
}

.muted {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-top: 0.5rem;
}
</style>
