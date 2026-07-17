<script setup>
import { computed } from 'vue'
import { PRIORITY_MAP } from '../constants'

const props = defineProps({
  priority: { type: String, default: 'MEDIUM' },
  dot: { type: Boolean, default: false },
})
const p = computed(() => PRIORITY_MAP[props.priority] || PRIORITY_MAP.MEDIUM)
</script>

<template>
  <span
    v-if="dot"
    class="inline-block h-2 w-2 rounded-full"
    :style="{ background: p.color }"
    :title="p.label"
  />
  <span
    v-else
    class="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium"
    :style="{ color: p.color, background: p.color + '18' }"
  >
    <span class="h-1.5 w-1.5 rounded-full" :style="{ background: p.color }" />
    {{ p.label }}
  </span>
</template>
