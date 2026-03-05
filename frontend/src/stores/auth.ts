import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface User {
  id: number
  username: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  let initialUser: User | null = null
  try {
    const s = localStorage.getItem('user')
    if (s) initialUser = JSON.parse(s)
  } catch {}
  const user = ref<User | null>(initialUser)

  const isLoggedIn = computed(() => !!token.value)

  function setLogin(t: string, u: User) {
    token.value = t
    user.value = u
    localStorage.setItem('token', t)
    localStorage.setItem('user', JSON.stringify(u))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isLoggedIn, setLogin, logout }
})
