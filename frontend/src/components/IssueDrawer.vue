<script setup>
import { onMounted, ref, watch } from 'vue'
import { epicApi, issueApi } from '../api'
import { BOARD_COLUMNS, PRIORITIES } from '../constants'
import { useIssueStore } from '../stores/issue'
import { useProjectStore } from '../stores/project'
import ActivityFeed from './ActivityFeed.vue'
import CommentThread from './CommentThread.vue'
import Icon from './Icon.vue'
import LabelChip from './LabelChip.vue'

const props = defineProps({ issueId: { type: Number, required: true } })
const emit = defineEmits(['close'])

const project = useProjectStore()
const issueStore = useIssueStore()

const issue = ref(null)
const epics = ref([])
const tab = ref('comments')
const addLabelId = ref(null)

async function load() {
  const { data } = await issueApi.get(props.issueId)
  issue.value = data
  if (project.current) epics.value = (await epicApi.list(project.current.id)).data
}
onMounted(load)
watch(() => props.issueId, load)

async function save(patch) {
  const { data } = await issueApi.update(props.issueId, patch)
  issue.value = data
  issueStore.replace(data)
}

async function attachLabel() {
  if (!addLabelId.value) return
  const { data } = await issueApi.addLabel(props.issueId, addLabelId.value)
  issue.value = data
  issueStore.replace(data)
  addLabelId.value = null
}
async function detachLabel(labelId) {
  const { data } = await issueApi.removeLabel(props.issueId, labelId)
  issue.value = data
  issueStore.replace(data)
}

async function removeIssue() {
  if (!confirm('이 이슈를 삭제할까요?')) return
  await issueApi.remove(props.issueId)
  issueStore.removeLocal(props.issueId)
  emit('close')
}

function availableLabels() {
  const attached = new Set((issue.value?.labels || []).map((l) => l.id))
  return project.labels.filter((l) => !attached.has(l.id))
}
</script>

<template>
  <div class="fixed inset-0 z-30 flex justify-end bg-slate-900/30 backdrop-blur-[2px]" @click.self="emit('close')">
    <aside
      class="w-full max-w-lg h-full overflow-auto bg-white shadow-2xl border-l border-slate-200"
    >
      <div v-if="issue" class="flex flex-col min-h-full">
        <!-- 헤더 -->
        <div class="sticky top-0 z-10 bg-white/90 backdrop-blur px-6 py-3.5 border-b border-slate-100 flex items-center justify-between">
          <span class="text-xs font-mono font-semibold text-slate-400">{{ issue.key }}</span>
          <div class="flex items-center gap-1">
            <button class="btn btn-ghost btn-xs !p-1.5 text-slate-400 hover:text-red-600" title="삭제" @click="removeIssue">
              <Icon name="trash" :size="17" />
            </button>
            <button class="btn btn-ghost btn-xs !p-1.5 text-slate-400" title="닫기" @click="emit('close')">
              <Icon name="close" :size="18" />
            </button>
          </div>
        </div>

        <div class="px-6 py-5 space-y-6 flex-1">
          <!-- 제목 -->
          <input
            :value="issue.title"
            class="w-full text-lg font-semibold text-slate-900 outline-none border-b border-transparent focus:border-indigo-300 pb-1 -mt-1"
            @change="(e) => save({ title: e.target.value })"
          />

          <!-- 속성 -->
          <div class="grid grid-cols-2 gap-x-4 gap-y-3.5">
            <label class="block">
              <span class="field-label">상태</span>
              <select :value="issue.status" class="input" @change="(e) => save({ status: e.target.value })">
                <option v-for="c in BOARD_COLUMNS" :key="c.key" :value="c.key">{{ c.label }}</option>
              </select>
            </label>
            <label class="block">
              <span class="field-label">우선순위</span>
              <select :value="issue.priority" class="input" @change="(e) => save({ priority: e.target.value })">
                <option v-for="p in PRIORITIES" :key="p.key" :value="p.key">{{ p.label }}</option>
              </select>
            </label>
            <label class="block">
              <span class="field-label">담당자</span>
              <select
                :value="issue.assignee_id ?? ''"
                class="input"
                @change="(e) => save({ assignee_id: e.target.value ? Number(e.target.value) : null })"
              >
                <option value="">미지정</option>
                <option v-for="u in project.users" :key="u.id" :value="u.id">{{ u.name }}</option>
              </select>
            </label>
            <label class="block">
              <span class="field-label">마감일</span>
              <input
                type="date"
                :value="issue.due_date ?? ''"
                class="input"
                @change="(e) => save({ due_date: e.target.value || null })"
              />
            </label>
            <label class="block col-span-2">
              <span class="field-label">에픽</span>
              <select
                :value="issue.epic_id ?? ''"
                class="input"
                @change="(e) => save({ epic_id: e.target.value ? Number(e.target.value) : null })"
              >
                <option value="">없음</option>
                <option v-for="ep in epics" :key="ep.id" :value="ep.id">{{ ep.key }} · {{ ep.title }}</option>
              </select>
            </label>
          </div>

          <!-- 라벨 -->
          <div>
            <span class="field-label">라벨</span>
            <div class="flex flex-wrap items-center gap-1.5">
              <LabelChip
                v-for="l in issue.labels"
                :key="l.id"
                :label="l"
                removable
                @remove="detachLabel(l.id)"
              />
              <select
                v-model="addLabelId"
                class="rounded-md border border-dashed border-slate-300 bg-white px-2 py-1 text-xs text-slate-500 hover:border-slate-400"
                @change="attachLabel"
              >
                <option :value="null">+ 라벨</option>
                <option v-for="l in availableLabels()" :key="l.id" :value="l.id">{{ l.name }}</option>
              </select>
            </div>
          </div>

          <!-- 설명 -->
          <div>
            <span class="field-label">설명</span>
            <textarea
              :value="issue.description ?? ''"
              rows="4"
              class="input resize-y"
              placeholder="설명 추가…"
              @change="(e) => save({ description: e.target.value })"
            />
          </div>

          <!-- 탭 -->
          <div>
            <div class="border-b border-slate-200 flex gap-1 text-sm">
              <button
                class="inline-flex items-center gap-1.5 px-3 py-2 -mb-px border-b-2 transition-colors"
                :class="tab === 'comments' ? 'border-indigo-600 text-indigo-700 font-medium' : 'border-transparent text-slate-500 hover:text-slate-700'"
                @click="tab = 'comments'"
              >
                <Icon name="comment" :size="15" /> 댓글
                <span v-if="issue.comment_count" class="text-xs text-slate-400">{{ issue.comment_count }}</span>
              </button>
              <button
                class="inline-flex items-center gap-1.5 px-3 py-2 -mb-px border-b-2 transition-colors"
                :class="tab === 'activity' ? 'border-indigo-600 text-indigo-700 font-medium' : 'border-transparent text-slate-500 hover:text-slate-700'"
                @click="tab = 'activity'"
              >
                <Icon name="activity" :size="15" /> 활동
              </button>
            </div>
            <div class="pt-4">
              <CommentThread v-if="tab === 'comments'" :issue-id="issueId" @changed="load" />
              <ActivityFeed v-else :issue-id="issueId" :key="issue.updated_at" />
            </div>
          </div>
        </div>
      </div>

      <div v-else class="p-6 text-slate-400 text-sm">불러오는 중…</div>
    </aside>
  </div>
</template>
