import { createRouter, createWebHistory } from 'vue-router'

// P0: 최소 라우팅. 실제 화면(로그인/보드/백로그/에픽/대시보드)은 P4~P7에서 확장.
const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
