<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">预测</h1>
        <div class="page-subtitle">多模型并行预测与指标对比，支持组合模型。</div>
      </div>
      <div class="tabs">
        <button class="tab" :class="{ active: activeTab === 'predict' }" @click="activeTab = 'predict'">预测对比</button>
        <button class="tab" :class="{ active: activeTab === 'train' }" @click="activeTab = 'train'">训练评估</button>
      </div>
    </div>

    <div v-if="activeTab === 'predict'" class="grid grid-predict">
      <div class="card">
        <div class="card-header">
          <div class="card-title">预测设置</div>
          <button class="btn btn-primary" :disabled="predicting || !predictModels.length" @click="doPredict">开始预测</button>
        </div>

        <div class="controls">
          <div class="control">
            <label>农产品</label>
            <select v-model="predictProduct">
              <option value="矮脚白菜">矮脚白菜</option>
              <option value="本地白菜">本地白菜</option>
              <option value="小塘白菜">小塘白菜</option>
              <option value="土豆">土豆</option>
            </select>
          </div>
          <div class="control">
            <label>预测天数</label>
            <select v-model="predictDays">
              <option :value="1">1 天</option>
              <option :value="3">3 天</option>
              <option :value="7">7 天</option>
            </select>
          </div>
          <div class="control">
            <label>使用天气特征</label>
            <select v-model="useWeather">
              <option :value="true">是</option>
              <option :value="false">否</option>
            </select>
          </div>
          <div class="control">
            <label>区间展示模型</label>
            <select v-model="bandModel">
              <option v-for="m in predictModels" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>
        </div>

        <div class="model-pick">
          <div class="row-head">
            <div class="model-title">预测模型（可多选）</div>
            <div class="row-actions">
              <button class="btn btn-secondary btn-sm" type="button" @click="predictModels = [...modelList]">全选</button>
              <button class="btn btn-secondary btn-sm" type="button" @click="predictModels = []">清空</button>
            </div>
          </div>
          <div class="check-row">
            <label v-for="m in modelList" :key="m">
              <input type="checkbox" :value="m" v-model="predictModels" />
              {{ m }}
            </label>
          </div>
          <div v-if="predictModels.includes(ensembleName)" class="ensemble-box">
            <div class="row-head">
              <div class="model-title">组合模型基模型</div>
              <div class="row-actions">
                <button class="btn btn-secondary btn-sm" type="button" @click="ensembleBaseModels = [...baseModelList]">全选</button>
                <button class="btn btn-secondary btn-sm" type="button" @click="ensembleBaseModels = []">清空</button>
              </div>
            </div>
            <div class="check-row">
              <label v-for="m in baseModelList" :key="m">
                <input type="checkbox" :value="m" v-model="ensembleBaseModels" />
                {{ m }}
              </label>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="charts">
          <div class="chart-block">
            <div class="chart-title">预测价格对比</div>
            <div ref="predChartRef" class="chart-container chart-sm"></div>
          </div>
          <div class="chart-block">
            <div class="chart-title">指标对比</div>
            <div ref="metricsChartRef" class="chart-container chart-sm"></div>
          </div>
        </div>
      </div>

      <div class="card span-2">
        <div class="card-header">
          <div class="card-title">预测明细</div>
        </div>
        <div v-if="!tableDates.length" class="empty">
          <div class="empty-title">暂无预测结果</div>
          <div class="empty-sub">选择模型后点击“开始预测”。</div>
        </div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>日期</th>
                <th v-for="m in tableModels" :key="m">{{ m }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in tableDates" :key="d">
                <td class="date-cell">{{ d }}</td>
                <td v-for="m in tableModels" :key="m">
                  <div v-if="getCell(m, d)" class="cell">
                    <div class="cell-main">{{ getCell(m, d)!.price_pred }}</div>
                    <div class="cell-sub" v-if="getCell(m, d)!.confidence_low != null && getCell(m, d)!.confidence_high != null">
                      {{ `[${getCell(m, d)!.confidence_low}, ${getCell(m, d)!.confidence_high}]` }}
                    </div>
                  </div>
                  <span v-else class="muted">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-else class="grid grid-train">
      <div class="card">
        <div class="card-header">
          <div class="card-title">后端训练结果</div>
          <button class="btn btn-secondary" :disabled="training" @click="loadTrainResults">刷新结果</button>
        </div>
        <div class="controls">
          <div class="control">
            <label>农产品</label>
            <select v-model="trainProduct">
              <option value="矮脚白菜">矮脚白菜</option>
              <option value="本地白菜">本地白菜</option>
              <option value="小塘白菜">小塘白菜</option>
              <option value="土豆">土豆</option>
            </select>
          </div>
          <div class="control">
            <label>显示条数</label>
            <select v-model="trainResultLimit">
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
        </div>

        <div v-if="!trainResults.length" class="empty">
          <div class="empty-title">暂无训练结果</div>
          <div class="empty-sub">请在后端执行训练任务，然后点击“刷新结果”。</div>
        </div>
        <div v-else class="train-results">
          <table class="data-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>农产品</th>
                <th>模型</th>
                <th>MAE</th>
                <th>RMSE</th>
                <th>MAPE (%)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in trainResults" :key="`${r.id}-${r.model_name}`">
                <td>{{ r.created_at ? r.created_at.replace('T', ' ').slice(0, 19) : '—' }}</td>
                <td>{{ r.product_name }}</td>
                <td>{{ r.model_name }}</td>
                <td>{{ r.mae != null ? r.mae.toFixed(4) : '—' }}</td>
                <td>{{ r.rmse != null ? r.rmse.toFixed(4) : '—' }}</td>
                <td>{{ r.mape != null ? r.mape.toFixed(2) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { predict as predictApi } from '@/api'
import type { MultiPredictResult } from '@/api/types'

const modelList = ref<string[]>([])
const ensembleName = '组合模型'
const baseModelList = computed(() => modelList.value.filter((m) => m !== ensembleName))
const activeTab = ref<'predict' | 'train'>('predict')

const trainProduct = ref('本地白菜')
const training = ref(false)
const trainResults = ref<{ id: number; product_name: string; model_name: string; mae?: number | null; rmse?: number | null; mape?: number | null; created_at?: string }[]>([])
const trainResultLimit = ref(50)
const cvFolds = ref(5)

const predictProduct = ref('本地白菜')
const predictModels = ref<string[]>([])
const predictDays = ref(7)
const predicting = ref(false)
const useWeather = ref(true)
const predictResult = ref<MultiPredictResult | null>(null)
const ensembleBaseModels = ref<string[]>([])
const bandModel = ref<string>('')

const predChartRef = ref<HTMLElement | null>(null)
const metricsChartRef = ref<HTMLElement | null>(null)
let predChart: echarts.ECharts | null = null
let metricsChart: echarts.ECharts | null = null

onMounted(async () => {
  try {
    const res = await predictApi.models()
    modelList.value = res.data?.models ?? ['ARIMA', 'LSTM', 'SVR', '随机森林', ensembleName]
  } catch {
    modelList.value = ['ARIMA', 'LSTM', 'SVR', '随机森林', ensembleName]
  }

  predictModels.value = [...modelList.value]
  ensembleBaseModels.value = [...baseModelList.value]
  bandModel.value = predictModels.value.includes(ensembleName) ? ensembleName : (predictModels.value[0] || '')
  await loadTrainResults()
})

async function loadTrainResults() {
  training.value = true
  try {
    const res = await predictApi.trainResults(trainProduct.value, trainResultLimit.value)
    trainResults.value = res.data?.results ?? []
  } catch {
    trainResults.value = []
  } finally {
    training.value = false
  }
}

async function doPredict() {
  predicting.value = true
  predictResult.value = null
  try {
    const res = await predictApi.predictMulti(
      predictProduct.value,
      predictModels.value,
      predictDays.value,
      useWeather.value,
      predictModels.value.includes(ensembleName) ? ensembleBaseModels.value : undefined,
      cvFolds.value,
      'walk_forward',
    )
    predictResult.value = res.data
    await nextTick()
    renderPredictionChart()
    renderMetricsChart()
  } catch (e: any) {
    predictResult.value = null
  } finally {
    predicting.value = false
  }
}

const tableModels = computed(() => predictResult.value?.results?.map((r) => r.model_name) ?? [])

const tableDates = computed(() => {
  const s = new Set<string>()
  for (const r of predictResult.value?.results ?? []) {
    for (const p of r.predictions ?? []) s.add(p.predict_date)
  }
  return Array.from(s).sort()
})

function getCell(modelName: string, date: string) {
  const r = predictResult.value?.results?.find((x) => x.model_name === modelName)
  return r?.predictions?.find((p) => p.predict_date === date)
}

function renderPredictionChart() {
  if (!predChartRef.value) return
  if (!predChart) predChart = echarts.init(predChartRef.value)

  const results = predictResult.value?.results ?? []
  const dates = tableDates.value
  if (!results.length || !dates.length) {
    predChart.clear()
    predChart.setOption({ title: { text: '暂无数据', left: 'center', top: 'middle', textStyle: { color: '#94a3b8' } } })
    return
  }

  const series: any[] = []
  for (const r of results) {
    const m = r.model_name
    const map = new Map(r.predictions.map((p) => [p.predict_date, p]))
    const data = dates.map((d) => (map.get(d)?.price_pred ?? null))
    series.push({ name: m, type: 'line', data, smooth: true, showSymbol: false, emphasis: { focus: 'series' } })
  }

  const band = results.find((r) => r.model_name === bandModel.value)
  if (band) {
    const map = new Map(band.predictions.map((p) => [p.predict_date, p]))
    const lows = dates.map((d) => map.get(d)?.confidence_low ?? null)
    const highs = dates.map((d) => map.get(d)?.confidence_high ?? null)
    const diffs = dates.map((_, i) => (lows[i] != null && highs[i] != null ? (highs[i] as number) - (lows[i] as number) : null))
    if (diffs.some((x) => x != null)) {
      series.unshift(
        {
          name: `${band.model_name}-low`,
          type: 'line',
          data: lows,
          stack: 'band',
          lineStyle: { opacity: 0 },
          symbol: 'none',
          tooltip: { show: false },
        },
        {
          name: `${band.model_name}-band`,
          type: 'line',
          data: diffs,
          stack: 'band',
          lineStyle: { opacity: 0 },
          symbol: 'none',
          areaStyle: { color: 'rgba(37, 99, 235, 0.12)' },
          tooltip: { show: false },
        },
      )
    }
  }

  predChart.setOption(
    {
      tooltip: { trigger: 'axis' },
      legend: { type: 'scroll' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', name: '元/公斤' },
      series,
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    },
    { notMerge: true },
  )
  predChart.resize()
}

function renderMetricsChart() {
  if (!metricsChartRef.value) return
  if (!metricsChart) metricsChart = echarts.init(metricsChartRef.value)

  const results = predictResult.value?.results ?? []
  if (!results.length) {
    metricsChart.clear()
    metricsChart.setOption({ title: { text: '暂无数据', left: 'center', top: 'middle', textStyle: { color: '#94a3b8' } } })
    return
  }

  const cats = ['MAE', 'RMSE', 'MAPE']
  const series = results
    .filter((r) => r.metrics)
    .map((r) => ({
      name: r.model_name,
      type: 'bar',
      data: [r.metrics!.mae, r.metrics!.rmse, r.metrics!.mape],
    }))

  metricsChart.setOption(
    {
      tooltip: { trigger: 'axis' },
      legend: { type: 'scroll' },
      xAxis: { type: 'category', data: cats },
      yAxis: { type: 'value' },
      series,
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    },
    { notMerge: true },
  )
  metricsChart.resize()
}

function resizeCharts() {
  predChart?.resize()
  metricsChart?.resize()
}

watch([predictResult, bandModel], () => {
  renderPredictionChart()
  renderMetricsChart()
})

watch(
  () => activeTab.value,
  async (tab) => {
    if (tab === 'predict') {
      await nextTick()
      try {
        predChart?.dispose()
        metricsChart?.dispose()
      } catch {
      }
      predChart = null
      metricsChart = null
      renderPredictionChart()
      renderMetricsChart()
    } else {
      try {
        predChart?.dispose()
        metricsChart?.dispose()
      } catch {
      }
      predChart = null
      metricsChart = null
      loadTrainResults()
    }
  },
)

watch([trainProduct, trainResultLimit], () => {
  if (activeTab.value === 'train') loadTrainResults()
})

watch(
  () => predictModels.value.slice().sort().join('|'),
  () => {
    if (!predictModels.value.includes(bandModel.value)) {
      bandModel.value = predictModels.value.includes(ensembleName) ? ensembleName : (predictModels.value[0] || '')
    }
  },
)

watch(
  () => baseModelList.value.join('|'),
  () => {
    if (!ensembleBaseModels.value.length) ensembleBaseModels.value = [...baseModelList.value]
  },
)

onMounted(() => {
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  try {
    predChart?.dispose()
    metricsChart?.dispose()
  } catch {
  }
})
</script>

<style scoped>
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.page-subtitle {
  margin-top: 0.25rem;
  color: var(--text-muted);
  font-size: 0.95rem;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.25rem;
  box-shadow: var(--shadow);
}

.tab {
  border: 0;
  background: transparent;
  padding: 0.5rem 0.9rem;
  border-radius: 999px;
  color: var(--text-muted);
  font-weight: 600;
}

.tab.active {
  background: var(--accent-gradient);
  color: #fff;
}

.grid {
  display: grid;
  gap: 1rem;
  align-items: start;
}

.grid-predict {
  grid-template-columns: 420px 1fr;
}

.grid-train {
  grid-template-columns: 1fr;
}

.span-2 {
  grid-column: 1 / -1;
}

.controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.control label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.control select {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
}

.model-pick {
  margin-top: 1.25rem;
}

.row-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.row-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-sm {
  padding: 0.45rem 0.75rem;
  font-size: 0.85rem;
}

.model-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0;
}

.check-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1rem;
}

.check-row label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.5rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--border-light);
  user-select: none;
}

.ensemble-box {
  margin-top: 0.9rem;
  padding-top: 0.9rem;
  border-top: 1px dashed var(--border);
}

.charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.chart-title {
  font-size: 0.95rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
}

.chart-sm {
  height: 360px;
  min-height: 320px;
}

.empty {
  border: 1px dashed var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  background: var(--border-light);
}

.empty-title {
  font-weight: 700;
  color: var(--text);
}

.empty-sub {
  margin-top: 0.25rem;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.table-wrap {
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
  min-width: 720px;
}

.data-table th,
.data-table td {
  padding: 0.6rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}

.data-table th {
  position: sticky;
  top: 0;
  background: var(--bg-card);
  z-index: 1;
  color: var(--text-muted);
  font-weight: 700;
}

.date-cell {
  white-space: nowrap;
  font-weight: 600;
}

.muted {
  color: var(--text-muted);
}

.cell-main {
  font-weight: 700;
}

.cell-sub {
  margin-top: 0.2rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

@media (max-width: 1100px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .charts {
    grid-template-columns: 1fr;
  }
}
</style>
