<template>
  <div class="page">
    <h1 class="page-title">价格分析</h1>

    <div class="card">
      <h2 class="card-title">时间序列：价格走势</h2>
      <div class="form-row">
        <div class="form-group">
          <label>产品</label>
          <select v-model="seriesProduct">
            <option value="矮脚白菜">矮脚白菜</option>
            <option value="本地白菜">本地白菜</option>
            <option value="小塘白菜">小塘白菜</option>
            <option value="土豆">土豆</option>
          </select>
        </div>
        <div class="form-group">
          <label>粒度</label>
          <select v-model="seriesFreq">
            <option value="D">日</option>
            <option value="W">周</option>
            <option value="M">月</option>
          </select>
        </div>
        <div class="form-group">
          <label>开始日期</label>
          <input v-model="seriesStart" type="date" />
        </div>
        <div class="form-group">
          <label>结束日期</label>
          <input v-model="seriesEnd" type="date" />
        </div>
        <button class="btn btn-primary" @click="loadSeries">查询</button>
      </div>
      <div ref="seriesChartRef" class="chart-container"></div>
    </div>

    <div class="card">
      <h2 class="card-title">多因素关联：相关性热力图</h2>
      <div class="form-row">
        <div class="form-group">
          <label>产品</label>
          <select v-model="corrProduct">
            <option value="矮脚白菜">矮脚白菜</option>
            <option value="本地白菜">本地白菜</option>
            <option value="小塘白菜">小塘白菜</option>
            <option value="土豆">土豆</option>
          </select>
        </div>
        <button class="btn btn-primary" @click="loadCorrelation">查询</button>
      </div>
      <div ref="corrChartRef" class="chart-container"></div>
    </div>

    <div class="card">
      <h2 class="card-title">农产品对比</h2>
      <div class="form-row">
        <div class="form-group">
          <label>产品（逗号分隔）</label>
          <input v-model="compareProducts" type="text" placeholder="本地白菜,土豆" />
        </div>
        <div class="form-group">
          <label>粒度</label>
          <select v-model="compareFreq">
            <option value="D">日</option>
            <option value="W">周</option>
            <option value="M">月</option>
          </select>
        </div>
        <button class="btn btn-primary" @click="loadCompare">查询</button>
      </div>
      <div ref="compareChartRef" class="chart-container"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { analysis } from '@/api'
import type { SeriesItem, CorrelationData, CompareItem } from '@/api/types'

const seriesChartRef = ref<HTMLElement | null>(null)
const corrChartRef = ref<HTMLElement | null>(null)
const compareChartRef = ref<HTMLElement | null>(null)

const seriesProduct = ref('本地白菜')
const seriesFreq = ref('D')
const seriesStart = ref('')
const seriesEnd = ref('')
const seriesData = ref<SeriesItem[]>([])

const corrProduct = ref('本地白菜')
const corrData = ref<CorrelationData | null>(null)

const compareProducts = ref('本地白菜,土豆')
const compareFreq = ref('D')
const compareData = ref<CompareItem[]>([])

let seriesChart: echarts.ECharts | null = null
let corrChart: echarts.ECharts | null = null
let compareChart: echarts.ECharts | null = null

async function loadSeries() {
  try {
    const res = await analysis.series(seriesProduct.value, {
      date_start: seriesStart.value || undefined,
      date_end: seriesEnd.value || undefined,
      freq: seriesFreq.value,
    })
    seriesData.value = res.data || []
    renderSeries()
  } catch {
    seriesData.value = []
    renderSeries()
  }
}

function renderSeries() {
  if (!seriesChartRef.value) return
  if (!seriesChart) seriesChart = echarts.init(seriesChartRef.value)
  const dates = seriesData.value.map((d) => d.record_date)
  const prices = seriesData.value.map((d) => d.price)
  seriesChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: '元/公斤' },
    series: [{ name: '价格', type: 'line', data: prices, smooth: true }],
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  })
}

async function loadCorrelation() {
  try {
    const res = await analysis.correlation(corrProduct.value, {
      date_start: seriesStart.value || undefined,
      date_end: seriesEnd.value || undefined,
    })
    corrData.value = res.data || null
    renderCorrelation()
  } catch {
    corrData.value = null
    renderCorrelation()
  }
}

function renderCorrelation() {
  if (!corrChartRef.value) return
  if (!corrChart) corrChart = echarts.init(corrChartRef.value)

  // clear previous option to avoid stale state
  corrChart.clear()

  const d = corrData.value
  if (!d || !Array.isArray(d.matrix) || !Array.isArray(d.columns) || d.columns.length === 0) {
    corrChart.setOption({ title: { text: '暂无数据', left: 'center' } })
    return
  }

  // Flatten numeric values and build heatmap data coordinates
  const data: [number, number, number][] = []
  const values: number[] = []
  d.matrix.forEach((row, i) => {
    row.forEach((v, j) => {
      const num = Number(v)
      if (Number.isFinite(num)) {
        const rounded = Math.round(num * 100) / 100
        data.push([j, i, rounded])
        values.push(rounded)
      }
      // skip non-numeric cells
    })
  })

  if (data.length === 0) {
    corrChart.setOption({ title: { text: '暂无有效数据', left: 'center' } })
    return
  }

  // determine visualMap range from actual data
  const min = Math.min(...values)
  const max = Math.max(...values)

  corrChart.setOption({
    tooltip: {
      position: 'top',
      formatter: function (params: any) {
        // params: { value: [xIdx, yIdx, val], seriesName, marker }
        const x = d.columns[params.value[0]]
        const y = d.columns[params.value[1]]
        const v = params.value[2]
        return `${x} ↔ ${y}: ${v}`
      },
    },
    grid: { left: '15%', right: '10%', top: '10%', bottom: '15%' },
    xAxis: { type: 'category', data: d.columns, splitArea: { show: true }, axisLabel: { rotate: 45 } },
    yAxis: { type: 'category', data: d.columns, splitArea: { show: true } },
    visualMap: { min: isFinite(min) ? min : -1, max: isFinite(max) ? max : 1, orient: 'horizontal', left: 'center', bottom: '0%' },
    series: [
      {
        name: '相关系数',
        type: 'heatmap',
        data,
        label: { show: true },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } },
      },
    ],
  }, { notMerge: true })

  // ensure the chart fits its container
  corrChart.resize()
}

// resize helper to handle window/container changes
function resizeCharts() {
  try {
    seriesChart?.resize()
    corrChart?.resize()
    compareChart?.resize()
  } catch (e) {
    // ignore resize errors
  }
}

onMounted(() => {
  loadSeries()
  loadCorrelation()
  loadCompare()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  try {
    seriesChart?.dispose()
    corrChart?.dispose()
    compareChart?.dispose()
  } catch (e) {
    // ignore
  }
})

async function loadCompare() {
  try {
    const res = await analysis.compare(compareProducts.value, {
      date_start: seriesStart.value || undefined,
      date_end: seriesEnd.value || undefined,
      freq: compareFreq.value,
    })
    compareData.value = res.data || []
    renderCompare()
  } catch {
    compareData.value = []
    renderCompare()
  }
}

function renderCompare() {
  if (!compareChartRef.value) return
  if (!compareChart) compareChart = echarts.init(compareChartRef.value)
  const products = [...new Set(compareData.value.map((d) => d.product_name))]
  const dates = [...new Set(compareData.value.map((d) => d.record_date))].sort()
  const series = products.map((p) => ({
    name: p,
    type: 'bar',
    data: dates.map((date) => {
      const r = compareData.value.find((d) => d.record_date === date && d.product_name === p)
      return r ? r.price : null
    }),
  }))
  compareChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: products },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: '元/公斤' },
    series,
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  })
}

watch([seriesChartRef, corrChartRef, compareChartRef], () => {
  if (seriesChartRef.value && seriesData.value.length) renderSeries()
  if (corrChartRef.value && corrData.value) renderCorrelation()
  if (compareChartRef.value && compareData.value.length) renderCompare()
})
</script>

<style scoped>
.form-row {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.form-row .form-group {
  margin-bottom: 0;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
}
</style>
