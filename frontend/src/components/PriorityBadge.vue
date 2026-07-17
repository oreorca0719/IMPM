<script setup>
import { computed } from 'vue'
import { PRIORITY_MAP } from '../constants'

const props = defineProps({ priority: { type: String, default: 'MEDIUM' } })
const p = computed(() => PRIORITY_MAP[props.priority] || PRIORITY_MAP.MEDIUM)
</script>

<template>
  <span
    class="inline-flex items-center rounded px-1.5 py-0.5 text-[11px] font-medium text-white"
    :style="{ background: p.color }"
  >
    {{ p.label }}
  </span>
</template>
