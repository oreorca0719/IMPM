<script setup>
import { reactive, ref, watch } from 'vue'
import draggable from 'vuedraggable'
import { epicApi, issueApi } from '../api'
import { BOARD_COLUMNS, PRIORITIES } from '../constants'
import { useIssueStore } from '../stores/issue'
import { useProjectStore } from '../stores/project'
import CreateIssueModal from '../components/CreateIssueModal.vue'
import Icon from '../components/Icon.vue'
import IssueCard from '../components/IssueCard.vue'

const project = useProjectStore()
const issueStore = useIssueStore()

const board = reactive({ TODO: [], IN_PROGRESS: [], DONE: [] })
const epics = ref([])
const toast = ref('')
const showCreate = ref(false)

// 컬럼별 색 점(상태 시각 구분)
const DOT = { TODO: '#94a3b8', IN_PROGRESS: '#6366f1', DONE: '#22c55e' }

// ── 정렬 ────────────────────────────────────────────────
const SORT_OPTIONS = [
  { key: 'manual', label: '수동 (드래그 순서)' },
  { key: 'created_desc', label: '최신 등록순' },
  { key: 'created_asc', label: '오래된 등록순' },
  { key: 'priority', label: '우선순위 높은순' },
  { key: 'due', label: '마감 임박순' },
  { key: 'assignee', label: '담당자별' },
  { key: 'reporter', label: '등록자별' },
]
const sortKey = ref(localStorage.getItem('impm_board_sort') || 'manual')
watch(sortKey, (v) => {
  localStorage.setItem('impm_board_sort', v)
  rebuild()
})

const PRIO_RANK = Object.fromEntries(PRIORITIES.map((p, i) => [p.key, i])) // LOW0..URGENT3
const uname = (id) => (id ? project.userMap[id]?.name || '' : '￿') // 미지정은 맨 뒤로
const dueVal = (i) => (i.due_date ? new Date(i.due_date).getTime() : Infinity)
const cmpStr = (a, b) => (a < b ? -1 : a > b ? 1 : 0)

const SORTERS = {
  manual: (a, b) => a.board_order - b.board_order,
  created_desc: (a, b) => cmpStr(b.created_at, a.created_at),
  created_asc: (a, b) => cmpStr(a.created_at, b.created_at),
  priority: (a, b) => (PRIO_RANK[b.priority] ?? -1) - (PRIO_RANK[a.priority] ?? -1) || a.board_order - b.board_order,
  due: (a, b) => dueVal(a) - dueVal(b) || a.board_order - b.board_order,
  assignee: (a, b) => uname(a.assignee_id).localeCompare(uname(b.assignee_id), 'ko') || a.board_order - b.board_order,
  reporter: (a, b) => uname(a.reporter_id).localeCompare(uname(b.reporter_id), 'ko') || a.board_order - b.board_order,
}

function rebuild() {
  const sorter = SORTERS[sortKey.value] || SORTERS.manual
  for (const col of BOARD_COLUMNS) board[col.key] = []
  for (const it of issueStore.issues) {
    if (!board[it.status]) board[it.status] = []
    board[it.status].push(it)
  }
  for (const key of Object.keys(board)) board[key].sort(sorter)
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
  if (!info) return
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
  await issueStore.create(project.current.id, payload)
  showCreate.value = false
  epics.value = (await epicApi.list(project.current.id)).data
  rebuild()
}

const countOf = (key) => board[key]?.length || 0
</script>

<template>
  <div class="px-8 py-6">
    <header class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-semibold text-slate-900">칸반 보드</h1>
        <p class="text-sm text-slate-400 mt-0.5">
          {{ sortKey === 'manual' ? '드래그로 상태·순서를 옮기세요' : '정렬 중 — 드래그로 상태 변경은 가능합니다' }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <label class="flex items-center gap-1.5 text-sm text-slate-500">
          <span class="text-xs">정렬</span>
          <select v-model="sortKey" class="input w-auto py-1.5 text-sm">
            <option v-for="o in SORT_OPTIONS" :key="o.key" :value="o.key">{{ o.label }}</option>
          </select>
        </label>
        <button class="btn btn-primary btn-md" @click="showCreate = true">
          <Icon name="plus" :size="16" /> 새 이슈
        </button>
      </div>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
      <section
        v-for="col in BOARD_COLUMNS"
        :key="col.key"
        class="flex flex-col rounded-xl bg-slate-100/70 p-3 min-h-[62vh]"
      >
        <div class="flex items-center gap-2 px-1.5 mb-3 shrink-0">
          <span class="h-2 w-2 rounded-full" :style="{ background: DOT[col.key] }" />
          <h2 class="text-sm font-semibold text-slate-700">{{ col.label }}</h2>
          <span class="text-xs font-medium text-slate-400 tabular-nums">
            {{ countOf(col.key) }}
          </span>
        </div>
        <!-- 드롭 영역이 컬럼 전체를 채우도록: relative + flex-1, draggable h-full -->
        <div class="relative flex-1">
          <draggable
            :list="board[col.key]"
            group="issues"
            item-key="id"
            :sort="sortKey === 'manual'"
            class="space-y-2 h-full min-h-[120px]"
            ghost-class="opacity-40"
            @change="(e) => onChange(e, col.key)"
          >
            <template #item="{ element }">
              <IssueCard :issue="element" />
            </template>
          </draggable>
          <p
            v-if="!countOf(col.key)"
            class="absolute inset-0 flex items-center justify-center text-xs text-slate-400 select-none pointer-events-none"
          >
            여기로 카드를 드래그하세요
          </p>
        </div>
      </section>
    </div>

    <CreateIssueModal
      v-if="showCreate"
      :epics="epics"
      @close="showCreate = false"
      @created="onCreated"
    />

    <transition
      enter-active-class="transition duration-200"
      enter-from-class="opacity-0 translate-y-2"
      leave-active-class="transition duration-200"
      leave-to-class="opacity-0"
    >
      <div
        v-if="toast"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm text-white shadow-lg"
      >
        {{ toast }}
      </div>
    </transition>
  </div>
</template>
