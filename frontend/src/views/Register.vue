<template>
  <div class="register-page">
    <div class="register-card card">
      <h1 class="title">注册</h1>
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
        <button type="submit" class="btn btn-primary full" :disabled="loading">注册</button>
      </form>
      <p class="footer">
        已有账号？<router-link to="/login">登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth as authApi } from '@/api'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await authApi.register(username.value, password.value)
    router.push('/login')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.register-card {
  width: 100%;
  max-width: 400px;
}

.title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}

.form .form-group input,
.form .form-group select {
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
