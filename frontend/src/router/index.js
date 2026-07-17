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
    path: '/',
    component: () => import('../components/AppShell.vue'),
    meta: { auth: true },
    children: [
      { path: '', redirect: '/board' },
      { path: 'board', name: 'board', component: () => import('../views/BoardView.vue') },
      { path: 'backlog', name: 'backlog', component: () => import('../views/BacklogView.vue') },
      { path: 'epics', name: 'epics', component: () => import('../views/EpicsView.vue') },
      { path: 'dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.isAuthed()) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthed()) {
    return { name: 'board' }
  }
})

export default router
