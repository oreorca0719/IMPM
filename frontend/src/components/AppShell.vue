<script setup>
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useProjectStore } from '../stores/project'
import Icon from './Icon.vue'
import IssueDrawer from './IssueDrawer.vue'
import UserAvatar from './UserAvatar.vue'

const auth = useAuthStore()
const project = useProjectStore()
const route = useRoute()
const router = useRouter()

const nav = [
  { to: '/board', label: '보드', icon: 'board' },
  { to: '/backlog', label: '백로그', icon: 'list' },
  { to: '/epics', label: '에픽', icon: 'epic' },
  { to: '/dashboard', label: '대시보드', icon: 'dashboard' },
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
  <div class="min-h-screen flex bg-slate-50 text-slate-800">
    <!-- 사이드바 -->
    <aside class="w-60 shrink-0 bg-white border-r border-slate-200 flex flex-col">
      <div class="px-5 py-5 flex items-center gap-2.5">
        <div class="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-sm">
          <span class="text-white font-bold text-sm">IM</span>
        </div>
        <div class="min-w-0">
          <div class="text-sm font-semibold text-slate-900 leading-tight">IMPM</div>
          <div class="text-xs text-slate-400 truncate">
            {{ project.current?.name || 'STRIPE' }}
          </div>
        </div>
      </div>

      <nav class="flex-1 px-3 space-y-0.5">
        <RouterLink
          v-for="n in nav"
          :key="n.to"
          :to="n.to"
          class="group flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
          active-class="!bg-indigo-50 !text-indigo-700"
        >
          <Icon :name="n.icon" :size="18" class="shrink-0 opacity-80" />
          {{ n.label }}
        </RouterLink>
      </nav>

      <div class="p-3 border-t border-slate-100">
        <div class="flex items-center gap-2.5 rounded-lg px-2 py-1.5">
          <UserAvatar :name="auth.user?.name || '?'" :size="30" />
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-slate-800 truncate">
              {{ auth.user?.name || '…' }}
            </div>
            <div class="text-xs text-slate-400 truncate">{{ auth.user?.email }}</div>
          </div>
          <button
            class="btn btn-ghost btn-xs !p-1.5 text-slate-400 hover:text-slate-700"
            title="로그아웃"
            @click="logout"
          >
            <Icon name="logout" :size="17" />
          </button>
        </div>
      </div>
    </aside>

    <!-- 본문 -->
    <main class="flex-1 min-w-0 overflow-auto">
      <RouterView />
    </main>

    <!-- 이슈 상세 Drawer -->
    <IssueDrawer
      v-if="route.query.issue"
      :issue-id="Number(route.query.issue)"
      @close="closeDrawer"
    />
  </div>
</template>
