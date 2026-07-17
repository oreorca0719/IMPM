<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { epicApi, issueApi } from '../api'
import { BOARD_COLUMNS, STATUS_LABEL } from '../constants'
import { useProjectStore } from '../stores/project'
import PriorityBadge from '../components/PriorityBadge.vue'
import UserAvatar from '../components/UserAvatar.vue'

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

const epicMap = computed(() => Object.fromEntries(epics.value.map((e) => [e.id, e])))

function openIssue(id) {
  router.replace({ query: { ...route.query, issue: id } })
}
</script>

<template>
  <div class="p-6 space-y-4">
    <h1 class="text-xl font-bold">백로그</h1>

    <!-- 필터 -->
    <div class="flex flex-wrap gap-2">
      <input
        v-model="filters.q"
        placeholder="제목 검색…"
        class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
      />
      <select v-model="filters.status" class="rounded-lg border border-slate-300 px-2 py-1.5 text-sm">
        <option value="">전체 상태</option>
        <option v-for="c in BOARD_COLUMNS" :key="c.key" :value="c.key">{{ c.label }}</option>
      </select>
      <select v-model="filters.assignee_id" class="rounded-lg border border-slate-300 px-2 py-1.5 text-sm">
        <option value="">전체 담당자</option>
        <option v-for="u in project.users" :key="u.id" :value="u.id">{{ u.name }}</option>
      </select>
      <select v-model="filters.epic_id" class="rounded-lg border border-slate-300 px-2 py-1.5 text-sm">
        <option value="">전체 에픽</option>
        <option v-for="e in epics" :key="e.id" :value="e.id">{{ e.key }}</option>
      </select>
    </div>

    <!-- 목록 -->
    <div class="bg-white rounded-xl border border-slate-200 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-slate-50 text-slate-500 text-left">
          <tr>
            <th class="px-4 py-2 font-medium">키</th>
            <th class="px-4 py-2 font-medium">제목</th>
            <th class="px-4 py-2 font-medium">상태</th>
            <th class="px-4 py-2 font-medium">우선순위</th>
            <th class="px-4 py-2 font-medium">담당자</th>
            <th class="px-4 py-2 font-medium">마감</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="i in issues"
            :key="i.id"
            class="border-t border-slate-100 hover:bg-slate-50 cursor-pointer"
            @click="openIssue(i.id)"
          >
            <td class="px-4 py-2 font-mono text-slate-400">{{ i.key }}</td>
            <td class="px-4 py-2">{{ i.title }}</td>
            <td class="px-4 py-2">{{ STATUS_LABEL[i.status] || i.status }}</td>
            <td class="px-4 py-2"><PriorityBadge :priority="i.priority" /></td>
            <td class="px-4 py-2">
              <UserAvatar v-if="i.assignee_id" :name="project.userMap[i.assignee_id]?.name || '?'" :size="22" />
              <span v-else class="text-slate-300">—</span>
            </td>
            <td class="px-4 py-2 text-slate-500">{{ i.due_date || '—' }}</td>
          </tr>
          <tr v-if="!issues.length">
            <td colspan="6" class="px-4 py-8 text-center text-slate-400">이슈가 없습니다.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
