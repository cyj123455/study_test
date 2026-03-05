<template>
  <div class="login-page">
    <div class="login-card card">
      <h1 class="title">农产品价格分析与预测系统</h1>
      <p class="subtitle">登录</p>
      <form @submit.prevent="submit" class="form">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="username" type="text" required placeholder="请输入用户名" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" required placeholder="请输入密码" />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary full" :disabled="loading">登录</button>
      </form>
      <p class="footer">
        没有账号？<router-link to="/register">注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { auth as authApi } from '@/api'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await authApi.login(username.value, password.value)
    auth.setLogin(res.data.access_token, res.data.user)
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.login-card {
  width: 100%;
  max-width: 400px;
}

.title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.25rem;
}

.subtitle {
  font-size: 0.95rem;
  color: var(--text-muted);
  margin-bottom: 1.5rem;
}

.form .form-group {
  max-width: none;
}

.form .form-group input {
  max-width: none;
}

.error {
  color: var(--danger);
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}

.full {
  width: 100%;
  margin-top: 0.5rem;
}

.footer {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: var(--text-muted);
}
</style>
