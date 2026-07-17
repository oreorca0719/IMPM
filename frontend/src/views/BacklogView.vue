<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { epicApi, issueApi } from '../api'
import { BOARD_COLUMNS, STATUS_LABEL } from '../constants'
import { useProjectStore } from '../stores/project'
import Icon from '../components/Icon.vue'
import PriorityBadge from '../components/PriorityBadge.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { fmtDate } from '../utils/datetime'

const project = useProjectStore()
const router = useRouter()
const route = useRoute()

const issues = ref([])
const epics = ref([])
const filters = ref({ status: '', assignee_id: '', epic_id: '', q: '' })

async function reload() {
  if (!project.current) return
  const params = {}
  for (const [k, v] of Object.entries(filters.value)) if (v) params[k] = v
  issues.value = (await issueApi.list(project.current.id, params)).data
}

watch(() => project.current, async (p) => {
  if (p) {
    epics.value = (await epicApi.list(p.id)).data
    await reload()
  }
}, { immediate: true })
watch(filters, reload, { deep: true })

function openIssue(id) {
  router.replace({ query: { ...route.query, issue: id } })
}
const statusChip = { TODO: 'bg-slate-100 text-slate-600', IN_PROGRESS: 'bg-indigo-50 text-indigo-700', DONE: 'bg-green-50 text-green-700' }
</script>

<template>
  <div class="px-8 py-6 space-y-5">
    <header>
      <h1 class="text-xl font-semibold text-slate-900">백로그</h1>
      <p class="text-sm text-slate-400 mt-0.5">전체 이슈 · 필터 검색</p>
    </header>

    <!-- 필터 -->
    <div class="flex flex-wrap gap-2">
      <div class="relative">
        <Icon name="search" :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input v-model="filters.q" placeholder="제목 검색…" class="input pl-9 w-56" />
      </div>
      <select v-model="filters.status" class="input w-auto">
        <option value="">전체 상태</option>
        <option v-for="c in BOARD_COLUMNS" :key="c.key" :value="c.key">{{ c.label }}</option>
      </select>
      <select v-model="filters.assignee_id" class="input w-auto">
        <option value="">전체 담당자</option>
        <option v-for="u in project.users" :key="u.id" :value="u.id">{{ u.name }}</option>
      </select>
      <select v-model="filters.epic_id" class="input w-auto">
        <option value="">전체 에픽</option>
        <option v-for="e in epics" :key="e.id" :value="e.id">{{ e.key }}</option>
      </select>
    </div>

    <!-- 목록 -->
    <div class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-xs text-slate-400 border-b border-slate-100">
            <th class="px-4 py-2.5 font-medium">키</th>
            <th class="px-4 py-2.5 font-medium">제목</th>
            <th class="px-4 py-2.5 font-medium">상태</th>
            <th class="px-4 py-2.5 font-medium">우선순위</th>
            <th class="px-4 py-2.5 font-medium">담당자</th>
            <th class="px-4 py-2.5 font-medium">마감</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="i in issues"
            :key="i.id"
            class="border-b border-slate-50 last:border-0 hover:bg-slate-50 cursor-pointer transition-colors"
            @click="openIssue(i.id)"
          >
            <td class="px-4 py-2.5 font-mono text-xs text-slate-400">{{ i.key }}</td>
            <td class="px-4 py-2.5 text-slate-800 font-medium">{{ i.title }}</td>
            <td class="px-4 py-2.5">
              <span class="rounded-md px-2 py-0.5 text-xs font-medium" :class="statusChip[i.status] || 'bg-slate-100 text-slate-600'">
                {{ STATUS_LABEL[i.status] || i.status }}
              </span>
            </td>
            <td class="px-4 py-2.5"><PriorityBadge :priority="i.priority" /></td>
            <td class="px-4 py-2.5">
              <UserAvatar v-if="i.assignee_id" :name="project.userMap[i.assignee_id]?.name || '?'" :size="22" />
              <span v-else class="text-slate-300">—</span>
            </td>
            <td class="px-4 py-2.5 text-slate-500 text-xs">{{ i.due_date ? fmtDate(i.due_date) : '—' }}</td>
          </tr>
          <tr v-if="!issues.length">
            <td colspan="6" class="px-4 py-12 text-center text-slate-400">
              <Icon name="list" :size="26" class="text-slate-300 mx-auto mb-2" />
              이슈가 없습니다.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
