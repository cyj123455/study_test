<template>
  <div class="page">
    <h1 class="page-title">异常预警</h1>
    <div class="card">
      <div class="form-row">
        <div class="form-group">
          <label>产品筛选</label>
          <select v-model="filterProduct">
            <option value="">全部</option>
            <option value="矮脚白菜">矮脚白菜</option>
            <option value="本地白菜">本地白菜</option>
            <option value="小塘白菜">小塘白菜</option>
            <option value="土豆">土豆</option>
          </select>
        </div>
        <div class="form-group">
          <label>状态</label>
          <select v-model="filterRead">
            <option :value="undefined">全部</option>
            <option :value="0">未读</option>
            <option :value="1">已读</option>
          </select>
        </div>
        <button class="btn btn-primary" @click="load">查询</button>
      </div>
      <div class="alert-list">
        <div v-for="a in list" :key="a.id" class="alert-item" :class="{ read: a.is_read }">
          <div class="alert-header">
            <span class="product">{{ a.product_name }}</span>
            <span class="date">{{ a.record_date }}</span>
            <span class="type">{{ a.alert_type }}</span>
            <button v-if="!a.is_read" class="btn btn-secondary small" @click="markRead(a.id)">标记已读</button>
          </div>
          <p v-if="a.reason" class="reason">{{ a.reason }}</p>
          <p v-if="a.price != null" class="price">价格：{{ a.price }} 元/公斤</p>
        </div>
      </div>
      <p v-if="list.length === 0 && !loading" class="muted">暂无预警记录</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { alerts as alertsApi } from '@/api'
import type { AlertItem } from '@/api/types'

const filterProduct = ref('')
const filterRead = ref<number | undefined>(undefined)
const list = ref<AlertItem[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await alertsApi.list({
      product_name: filterProduct.value || undefined,
      is_read: filterRead.value,
      limit: 100,
    })
    list.value = res.data || []
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

async function markRead(id: number) {
  try {
    await alertsApi.markRead(id)
    const i = list.value.findIndex((a) => a.id === id)
    if (i >= 0) list.value[i].is_read = 1
  } catch {}
}

onMounted(load)
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

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.alert-item {
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-card);
}

.alert-item.read {
  opacity: 0.75;
  background: var(--bg-page);
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.alert-header .product {
  font-weight: 600;
}

.alert-header .date {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.alert-header .type {
  font-size: 0.85rem;
  padding: 0.2rem 0.5rem;
  background: var(--warning);
  color: #fff;
  border-radius: 4px;
}

.alert-header .small {
  margin-left: auto;
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
}

.reason {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.price {
  margin-top: 0.25rem;
  font-size: 0.9rem;
}

.muted {
  color: var(--text-muted);
  font-size: 0.9rem;
}
</style>
