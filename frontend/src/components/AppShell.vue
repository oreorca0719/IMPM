<script setup>
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useProjectStore } from '../stores/project'
import IssueDrawer from './IssueDrawer.vue'
import UserAvatar from './UserAvatar.vue'

const auth = useAuthStore()
const project = useProjectStore()
const route = useRoute()
const router = useRouter()

const nav = [
  { to: '/board', label: '보드', icon: '▤' },
  { to: '/backlog', label: '백로그', icon: '≣' },
  { to: '/epics', label: '에픽', icon: '◇' },
  { to: '/dashboard', label: '대시보드', icon: '📊' },
]

onMounted(async () => {
  if (!auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      /* 인터셉터가 401 처리 */
    }
  }
  if (!project.ready) await project.bootstrap()
})

function logout() {
  auth.logout()
  router.push('/login')
}

function closeDrawer() {
  const q = { ...route.query }
  delete q.issue
  router.replace({ query: q })
}
</script>

<template>
  <div class="min-h-screen flex bg-slate-100 text-slate-800">
    <!-- 사이드바 -->
    <aside class="w-52 shrink-0 bg-slate-900 text-slate-200 flex flex-col">
      <div class="px-5 py-4 border-b border-slate-700/60">
        <div class="text-lg font-bold text-white">IMPM</div>
        <div class="text-xs text-slate-400">
          {{ project.current?.name || 'STRIPE' }} 관리
        </div>
      </div>
      <nav class="flex-1 p-2 space-y-1">
        <RouterLink
          v-for="n in nav"
          :key="n.to"
          :to="n.to"
          class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-slate-800"
          active-class="bg-brand-600 text-white hover:bg-brand-600"
        >
          <span class="w-4 text-center">{{ n.icon }}</span>{{ n.label }}
        </RouterLink>
      </nav>
      <div class="p-3 border-t border-slate-700/60 flex items-center gap-2">
        <UserAvatar :name="auth.user?.name || '?'" />
        <div class="flex-1 min-w-0">
          <div class="text-sm truncate">{{ auth.user?.name || '…' }}</div>
        </div>
        <button class="text-xs text-slate-400 hover:text-white" @click="logout">
          로그아웃
        </button>
      </div>
    </aside>

    <!-- 본문 -->
    <main class="flex-1 min-w-0 overflow-auto">
      <RouterView />
    </main>

    <!-- 이슈 상세 Drawer (어느 화면에서든 ?issue=<id>) -->
    <IssueDrawer
      v-if="route.query.issue"
      :issue-id="Number(route.query.issue)"
      @close="closeDrawer"
    />
  </div>
</template>
