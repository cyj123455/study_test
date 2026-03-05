import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { guest: true } },
    { path: '/register', name: 'Register', component: () => import('@/views/Register.vue'), meta: { guest: true } },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
        { path: 'data', name: 'Data', component: () => import('@/views/DataManage.vue') },
        { path: 'analysis', name: 'Analysis', component: () => import('@/views/Analysis.vue') },
        { path: 'predict', name: 'Predict', component: () => import('@/views/Predict.vue') },
        { path: 'alerts', name: 'Alerts', component: () => import('@/views/Alerts.vue') },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) return next('/login')
  if (to.meta.guest && token) return next('/')
  next()
})

export default router
