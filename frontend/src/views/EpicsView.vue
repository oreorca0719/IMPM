<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { epicApi, issueApi } from '../api'
import { STATUS_LABEL } from '../constants'
import { useProjectStore } from '../stores/project'
import EpicProgressBar from '../components/EpicProgressBar.vue'
import Icon from '../components/Icon.vue'

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
  <div class="px-8 py-6 max-w-4xl">
    <header class="mb-6">
      <h1 class="text-xl font-semibold text-slate-900">에픽</h1>
      <p class="text-sm text-slate-400 mt-0.5">큰 작업 단위별 진행률</p>
    </header>

    <div class="flex gap-2 mb-5">
      <input
        v-model="newTitle"
        placeholder="새 에픽 제목…"
        class="input flex-1 max-w-md"
        @keyup.enter="createEpic"
      />
      <button :disabled="creating" class="btn btn-primary btn-md" @click="createEpic">
        <Icon name="plus" :size="16" /> 에픽 추가
      </button>
    </div>

    <div class="space-y-3">
      <div v-for="e in epics" :key="e.id" class="card p-4 hover:border-slate-300 transition-colors">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2 min-w-0">
            <Icon name="epic" :size="16" class="text-indigo-500 shrink-0" />
            <span class="font-mono text-xs text-slate-400">{{ e.key }}</span>
            <span class="font-medium text-slate-800 truncate">{{ e.title }}</span>
            <span class="text-xs text-slate-400 shrink-0">· {{ STATUS_LABEL[e.status] || e.status }}</span>
          </div>
          <button
            class="btn btn-ghost btn-xs shrink-0 inline-flex items-center gap-1"
            @click="toggleIssues(e)"
          >
            이슈 {{ issuesByEpic[e.id] ? '접기' : '보기' }}
            <Icon name="chevron" :size="13" :class="issuesByEpic[e.id] ? 'rotate-90' : ''" class="transition-transform" />
          </button>
        </div>
        <div class="mt-3 flex items-center gap-3">
          <EpicProgressBar :percent="e.percent" class="flex-1" />
          <span class="text-xs font-medium text-slate-500 w-24 text-right tabular-nums">
            {{ e.done }}/{{ e.total }} · {{ e.percent }}%
          </span>
        </div>
        <ul v-if="issuesByEpic[e.id]" class="mt-3 space-y-1 border-t border-slate-100 pt-3">
          <li
            v-for="i in issuesByEpic[e.id]"
            :key="i.id"
            class="flex items-center gap-2 text-sm text-slate-600 hover:text-indigo-600 cursor-pointer py-0.5"
            @click="openIssue(i.id)"
          >
            <span class="font-mono text-xs text-slate-400">{{ i.key }}</span>
            <span class="truncate">{{ i.title }}</span>
            <span class="text-xs text-slate-400 shrink-0">({{ STATUS_LABEL[i.status] || i.status }})</span>
          </li>
          <li v-if="!issuesByEpic[e.id].length" class="text-sm text-slate-400 py-1">이슈 없음</li>
        </ul>
      </div>

      <div v-if="!epics.length" class="card p-10 text-center">
        <Icon name="epic" :size="28" class="text-slate-300 mx-auto mb-2" />
        <p class="text-sm text-slate-400">에픽이 없습니다. 위에서 추가해 보세요.</p>
      </div>
    </div>
  </div>
</template>
