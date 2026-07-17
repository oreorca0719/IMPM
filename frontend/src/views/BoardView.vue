<script setup>
import { reactive, ref, watch } from 'vue'
import draggable from 'vuedraggable'
import { epicApi, issueApi } from '../api'
import { BOARD_COLUMNS } from '../constants'
import { useIssueStore } from '../stores/issue'
import { useProjectStore } from '../stores/project'
import CreateIssueModal from '../components/CreateIssueModal.vue'
import IssueCard from '../components/IssueCard.vue'

const project = useProjectStore()
const issueStore = useIssueStore()

// 상태별 컬럼 로컬 배열(vuedraggable v-model 대상)
const board = reactive({ TODO: [], IN_PROGRESS: [], DONE: [] })
const epics = ref([])
const toast = ref('')
const showCreate = ref(false)

function rebuild() {
  for (const col of BOARD_COLUMNS) board[col.key] = []
  const sorted = [...issueStore.issues].sort((a, b) => a.board_order - b.board_order)
  for (const it of sorted) {
    if (board[it.status]) board[it.status].push(it)
    else (board[it.status] = [it]) // 확장 상태 방어
  }
}

async function reload() {
  if (!project.current) return
  await issueStore.load(project.current.id)
  const { data } = await epicApi.list(project.current.id)
  epics.value = data
  rebuild()
}

watch(() => project.current, (p) => { if (p) reload() }, { immediate: true })
watch(() => issueStore.issues, rebuild)

function computeOrder(list, index) {
  const prev = list[index - 1]?.board_order
  const next = list[index + 1]?.board_order
  if (prev == null && next == null) return 1
  if (prev == null) return next - 1
  if (next == null) return prev + 1
  return (prev + next) / 2
}

async function onChange(evt, status) {
  const info = evt.added || evt.moved
  if (!info) return // removed 는 대상 컬럼의 added 로 처리됨
  const item = info.element
  const order = computeOrder(board[status], info.newIndex)
  const prev = { status: item.status, board_order: item.board_order }
  item.status = status
  item.board_order = order
  try {
    const { data } = await issueApi.move(item.id, status, order)
    issueStore.replace(data)
  } catch (e) {
    item.status = prev.status
    item.board_order = prev.board_order
    toast.value = '이동에 실패해 되돌렸습니다.'
    setTimeout(() => (toast.value = ''), 2500)
    await reload()
  }
}

async function onCreated(payload) {
  const created = await issueStore.create(project.current.id, payload)
  showCreate.value = false
  epics.value = (await epicApi.list(project.current.id)).data
  rebuild()
  return created
}

function countOf(key) {
  return board[key]?.length || 0
}
</script>

<template>
  <div class="p-6">
    <header class="flex items-center justify-between mb-5">
      <h1 class="text-xl font-bold">칸반 보드</h1>
      <button
        class="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        @click="showCreate = true"
      >
        + 이슈
      </button>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <section
        v-for="col in BOARD_COLUMNS"
        :key="col.key"
        class="bg-slate-200/60 rounded-xl p-3 min-h-[60vh]"
      >
        <div class="flex items-center justify-between px-1 mb-3">
          <h2 class="text-sm font-semibold text-slate-700">{{ col.label }}</h2>
          <span class="text-xs text-slate-500 bg-slate-300/70 rounded-full px-2">
            {{ countOf(col.key) }}
          </span>
        </div>
        <draggable
          :list="board[col.key]"
          group="issues"
          item-key="id"
          class="space-y-2 min-h-[40px]"
          ghost-class="opacity-40"
          @change="(e) => onChange(e, col.key)"
        >
          <template #item="{ element }">
            <IssueCard :issue="element" />
          </template>
        </draggable>
      </section>
    </div>

    <CreateIssueModal
      v-if="showCreate"
      :epics="epics"
      @close="showCreate = false"
      @created="onCreated"
    />

    <div
      v-if="toast"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 rounded-lg bg-red-600 px-4 py-2 text-sm text-white shadow-lg"
    >
      {{ toast }}
    </div>
  </div>
</template>
