import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    // 최초 로그인 시 아이디·비밀번호 변경(앱 셸 없이 단독 화면)
    path: '/setup',
    name: 'setup',
    component: () => import('../views/SetupView.vue'),
    meta: { auth: true },
  },
  {
    path: '/',
    component: () => import('../components/AppShell.vue'),
    meta: { auth: true },
    children: [
      { path: '', redirect: '/board' },
      { path: 'board', name: 'board', component: () => import('../views/BoardView.vue') },
      { path: 'backlog', name: 'backlog', component: () => import('../views/BacklogView.vue') },
      { path: 'epics', name: 'epics', component: () => import('../views/EpicsView.vue') },
      { path: 'dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
      { path: 'settings', name: 'settings', component: () => import('../views/SettingsView.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    return auth.isAuthed() && to.name === 'login' ? { name: 'board' } : true
  }

  if (!auth.isAuthed()) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // 사용자 정보가 없으면 먼저 조회(최초 변경 필요 여부 판단에 필요)
  if (!auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      auth.logout()
      return { name: 'login' }
    }
  }

  // 최초 변경이 끝날 때까지 다른 화면 접근 차단
  if (auth.needsSetup && to.name !== 'setup') return { name: 'setup' }
  if (!auth.needsSetup && to.name === 'setup') return { name: 'board' }
  return true
})

export default router
