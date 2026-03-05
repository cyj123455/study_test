<template>
  <div class="page">
    <h1 class="page-title">
      <span>🌾 综合仪表盘</span>
    </h1>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">🥬</div>
        <div class="stat-label">当日白菜均价</div>
        <div class="stat-value">{{ data?.today_cabbage_price != null ? data.today_cabbage_price.toFixed(2) : '—' }}</div>
        <div class="stat-unit">元/公斤</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🥔</div>
        <div class="stat-label">当日土豆均价</div>
        <div class="stat-value">{{ data?.today_potato_price != null ? data.today_potato_price.toFixed(2) : '—' }}</div>
        <div class="stat-unit">元/公斤</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⚠️</div>
        <div class="stat-label">未读预警</div>
        <div class="stat-value">{{ data?.alert_unread_count ?? 0 }}</div>
        <div class="stat-unit">条</div>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">预测准确率 TOP3 模型</h2>
      </div>
      <div v-if="data?.top3_models?.length" class="top-models">
        <div v-for="(m, i) in data.top3_models" :key="i" class="model-row">
          <span class="rank">{{ i + 1 }}</span>
          <div class="model-info">
            <div class="product">{{ m.product_name }}</div>
            <div class="model">{{ m.model_name }}</div>
          </div>
          <div class="mape-container">
            <div class="mape-label">MAPE</div>
            <div class="mape-value">{{ m.mape != null ? m.mape.toFixed(2) + '%' : '—' }}</div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <div class="empty-state-icon">🎯</div>
        <div class="empty-state-title">暂无训练记录</div>
        <div class="empty-state-description">请先在「预测」页训练模型</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dashboard } from '@/api'
import type { DashboardData } from '@/api/types'

const data = ref<DashboardData | null>(null)

onMounted(async () => {
  try {
    const res = await dashboard.get()
    data.value = res.data
  } catch {
    data.value = null
  }
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 1.5rem;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  transition: var(--transition);
  position: relative;
  overflow: hidden;
  text-align: center;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--accent-gradient);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.stat-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
  display: block;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 0.25rem;
}

.stat-unit {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.top-models {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.model-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1rem;
  border-radius: var(--radius-sm);
  background: var(--border-light);
  transition: var(--transition);
}

.model-row:hover {
  background: var(--border);
  transform: translateX(4px);
}

.rank {
  width: 32px;
  height: 32px;
  background: var(--accent-gradient);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 600;
  flex-shrink: 0;
}

.model-info {
  flex: 1;
}

.product {
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.25rem;
}

.model {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.mape-container {
  text-align: right;
}

.mape-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.mape-value {
  font-weight: 600;
  color: var(--accent);
  font-size: 1.1rem;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-muted);
}

.empty-state-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--text);
}

.empty-state-description {
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .model-row {
    flex-direction: column;
    text-align: center;
    gap: 0.75rem;
  }
  
  .mape-container {
    text-align: center;
  }
}
</style>