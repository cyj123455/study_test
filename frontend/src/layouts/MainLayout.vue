<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-text">农产品价格预测</div>
      </div>
      <nav class="nav">
        <router-link to="/" class="nav-item" active-class="active">
          <span class="nav-text">仪表盘</span>
        </router-link>
        <router-link to="/data" class="nav-item" active-class="active">
          <span class="nav-text">数据管理</span>
        </router-link>
        <router-link to="/analysis" class="nav-item" active-class="active">
          <span class="nav-text">价格分析</span>
        </router-link>
        <router-link to="/predict" class="nav-item" active-class="active">
          <span class="nav-text">预测</span>
        </router-link>
        <router-link to="/alerts" class="nav-item" active-class="active">
          <span class="nav-text">异常预警</span>
          <span v-if="alertCount > 0" class="badge">{{ alertCount }}</span>
        </router-link>
      </nav>
      <div class="user">
        <div class="user-info">
          <div class="user-avatar">{{ auth.user?.username?.charAt(0) || 'U' }}</div>
          <span class="username">{{ auth.user?.username }}</span>
        </div>
        <button class="btn btn-secondary" @click="handleLogout">
          <span class="nav-text">退出</span>
        </button>
      </div>
    </aside>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { dashboard } from '@/api'

const router = useRouter()
const auth = useAuthStore()

const alertCount = ref(0)

onMounted(async () => {
  try {
    const res = await dashboard.get()
    alertCount.value = res.data.alert_unread_count ?? 0
  } catch {
    // ignore
  }
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-page);
}

.sidebar {
  width: 240px;
  background: var(--bg-sidebar);
  color: #e8f0ed;
  display: flex;
  flex-direction: column;
  padding: 1.5rem 0;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 100;
  transition: var(--transition);
}

.logo {
  display: flex;
  align-items: center;
  font-size: 1.05rem;
  font-weight: 700;
  padding: 0 1.5rem 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  margin-bottom: 1.5rem;
  color: #fff;
}

.nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0 0.75rem;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  color: rgba(255,255,255,0.85);
  font-weight: 500;
  border-radius: var(--radius-sm);
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 4px;
  background: var(--accent-light);
  transform: scaleY(0);
  transition: var(--transition);
}

.nav-item:hover {
  background: var(--bg-sidebar-hover);
  color: #fff;
}

.nav-item:hover::before {
  transform: scaleY(1);
}

.nav-item.active {
  background: rgba(56, 161, 105, 0.2);
  color: #fff;
  font-weight: 600;
}

.nav-item.active::before {
  transform: scaleY(1);
}

.nav-icon {
  display: none;
}

.nav-text {
  flex: 1;
}

.badge {
  background: var(--warning);
  color: #fff;
  font-size: 0.75rem;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-weight: 600;
  min-width: 24px;
  text-align: center;
}

.user {
  padding: 1.5rem;
  border-top: 1px solid rgba(255,255,255,0.1);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--accent-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #fff;
  font-size: 1rem;
}

.username {
  font-size: 0.95rem;
  color: rgba(255,255,255,0.9);
  font-weight: 500;
}

.user .btn {
  padding: 0.75rem;
  font-size: 0.85rem;
  background: rgba(255,255,255,0.15);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: var(--transition);
}

.user .btn:hover {
  background: rgba(255,255,255,0.25);
  transform: translateY(-1px);
}

.main {
  flex: 1;
  overflow: auto;
  background: var(--bg-page);
  position: relative;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    width: 200px;
  }
  
  .logo-text {
    font-size: 1rem;
  }
  
  .nav-item {
    padding: 0.6rem 0.8rem;
  }
  
  .nav-text {
    font-size: 0.85rem;
  }
}
</style>
