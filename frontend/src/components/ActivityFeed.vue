<script setup>
import { onMounted, ref, watch } from 'vue'
import { commentApi } from '../api'
import { useProjectStore } from '../stores/project'
import { PRIORITY_MAP, STATUS_LABEL } from '../constants'

const props = defineProps({ issueId: { type: Number, required: true } })
const project = useProjectStore()
const logs = ref([])

async function load() {
  logs.value = (await commentApi.activity(props.issueId)).data
}
onMounted(load)
watch(() => props.issueId, load)

function actor(id) {
  return project.userMap[id]?.name || '누군가'
}
function fmt(ts) {
  return new Date(ts).toLocaleString('ko-KR')
}

function statusText(v) {
  return v ? STATUS_LABEL[v] || v : '없음'
}
function priorityText(v) {
  return v ? PRIORITY_MAP[v]?.label || v : '없음'
}
function userText(id) {
  return id ? project.userMap[Number(id)]?.name || `#${id}` : '미지정'
}

function describe(log) {
  const who = actor(log.actor_id)
  switch (log.action) {
    case 'created':
      return `${who}이(가) 이슈를 생성했습니다.`
    case 'status_changed':
      return `${who}이(가) 상태를 ${statusText(log.old_value)} → ${statusText(log.new_value)} 로 변경했습니다.`
    case 'assignee_changed':
      return `${who}이(가) 담당자를 ${userText(log.old_value)} → ${userText(log.new_value)} 로 변경했습니다.`
    case 'due_changed':
      return `${who}이(가) 마감일을 ${log.old_value || '없음'} → ${log.new_value || '없음'} 로 변경했습니다.`
    case 'priority_changed':
      return `${who}이(가) 우선순위를 ${priorityText(log.old_value)} → ${priorityText(log.new_value)} 로 변경했습니다.`
    case 'epic_changed':
      return `${who}이(가) 에픽을 변경했습니다.`
    default:
      return `${who}이(가) ${log.action}`
  }
}
</script>

<template>
  <div class="space-y-3">
    <div v-if="!logs.length" class="text-sm text-slate-400">활동 내역이 없습니다.</div>
    <div v-for="log in logs" :key="log.id" class="flex gap-2 text-sm">
      <span class="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
      <div>
        <p>{{ describe(log) }}</p>
        <p class="text-xs text-slate-400">{{ fmt(log.created_at) }}</p>
      </div>
    </div>
  </div>
</template>
