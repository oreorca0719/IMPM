<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { epicApi, issueApi } from '../api'
import { STATUS_LABEL } from '../constants'
import { useProjectStore } from '../stores/project'
import EpicProgressBar from '../components/EpicProgressBar.vue'

const project = useProjectStore()
const router = useRouter()
const route = useRoute()

const epics = ref([])
const issuesByEpic = ref({})
const newTitle = ref('')
const creating = ref(false)

async function reload() {
  if (!project.current) return
  epics.value = (await epicApi.list(project.current.id)).data
}
watch(() => project.current, (p) => { if (p) reload() }, { immediate: true })

async function createEpic() {
  if (!newTitle.value.trim()) return
  creating.value = true
  try {
    await epicApi.create(project.current.id, { title: newTitle.value })
    newTitle.value = ''
    await reload()
  } finally {
    creating.value = false
  }
}

async function toggleIssues(epic) {
  if (issuesByEpic.value[epic.id]) {
    delete issuesByEpic.value[epic.id]
    return
  }
  const { data } = await issueApi.list(project.current.id, { epic_id: epic.id })
  issuesByEpic.value[epic.id] = data
}

function openIssue(id) {
  router.replace({ query: { ...route.query, issue: id } })
}
</script>

<template>
  <div class="p-6 space-y-5">
    <h1 class="text-xl font-bold">에픽</h1>

    <div class="flex gap-2">
      <input
        v-model="newTitle"
        placeholder="새 에픽 제목…"
        class="flex-1 max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
        @keyup.enter="createEpic"
      />
      <button
        :disabled="creating"
        class="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700 disabled:opacity-60"
        @click="createEpic"
      >
        에픽 추가
      </button>
    </div>

    <div class="space-y-3">
      <div v-for="e in epics" :key="e.id" class="bg-white rounded-xl border border-slate-200 p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="font-mono text-xs text-slate-400">{{ e.key }}</span>
            <span class="font-medium">{{ e.title }}</span>
            <span class="text-xs text-slate-400">· {{ STATUS_LABEL[e.status] || e.status }}</span>
          </div>
          <button class="text-xs text-brand-600 hover:underline" @click="toggleIssues(e)">
            이슈 {{ issuesByEpic[e.id] ? '접기' : '보기' }}
          </button>
        </div>
        <div class="mt-3 flex items-center gap-3">
          <EpicProgressBar :percent="e.percent" class="flex-1" />
          <span class="text-xs text-slate-500 w-24 text-right">
            {{ e.done }}/{{ e.total }} · {{ e.percent }}%
          </span>
        </div>
        <ul v-if="issuesByEpic[e.id]" class="mt-3 space-y-1 border-t border-slate-100 pt-2">
          <li
            v-for="i in issuesByEpic[e.id]"
            :key="i.id"
            class="flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600 cursor-pointer"
            @click="openIssue(i.id)"
          >
            <span class="font-mono text-xs text-slate-400">{{ i.key }}</span>
            {{ i.title }}
            <span class="text-xs text-slate-400">({{ STATUS_LABEL[i.status] || i.status }})</span>
          </li>
          <li v-if="!issuesByEpic[e.id].length" class="text-sm text-slate-400">이슈 없음</li>
        </ul>
      </div>
      <div v-if="!epics.length" class="text-slate-400 text-sm">에픽이 없습니다. 위에서 추가해 보세요.</div>
    </div>
  </div>
</template>
