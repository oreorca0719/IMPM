<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import LabelChip from './LabelChip.vue'
import PriorityBadge from './PriorityBadge.vue'
import UserAvatar from './UserAvatar.vue'

const props = defineProps({ issue: { type: Object, required: true } })
const project = useProjectStore()
const router = useRouter()
const route = useRoute()

const assignee = computed(() =>
  props.issue.assignee_id ? project.userMap[props.issue.assignee_id] : null,
)

const dueInfo = computed(() => {
  if (!props.issue.due_date) return null
  const due = new Date(props.issue.due_date)
  const days = Math.ceil((due - new Date()) / 86400000)
  return { text: props.issue.due_date, soon: days <= 7, over: days < 0 }
})

function open() {
  router.replace({ query: { ...route.query, issue: props.issue.id } })
}
</script>

<template>
  <div
    class="bg-white rounded-lg border border-slate-200 p-3 shadow-sm hover:shadow cursor-pointer space-y-2"
    @click="open"
  >
    <div class="flex items-center justify-between">
      <span class="text-xs font-mono text-slate-400">{{ issue.key }}</span>
      <PriorityBadge :priority="issue.priority" />
    </div>
    <div class="text-sm font-medium leading-snug">{{ issue.title }}</div>
    <div v-if="issue.labels?.length" class="flex flex-wrap gap-1">
      <LabelChip v-for="l in issue.labels" :key="l.id" :label="l" />
    </div>
    <div class="flex items-center justify-between pt-1">
      <span
        v-if="dueInfo"
        class="text-[11px]"
        :class="dueInfo.over ? 'text-red-600 font-semibold' : dueInfo.soon ? 'text-amber-600' : 'text-slate-400'"
      >
        📅 {{ dueInfo.text }}
      </span>
      <span v-else />
      <UserAvatar v-if="assignee" :name="assignee.name" :size="24" />
    </div>
  </div>
</template>
