<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, default: '' },
  size: { type: Number, default: 28 },
})

const initial = computed(() => (props.name ? props.name.trim().slice(0, 1) : '?'))
// 이름 기반 안정적 파스텔 컬러
const bg = computed(() => {
  let h = 0
  for (const ch of props.name) h = (h * 31 + ch.charCodeAt(0)) % 360
  return `hsl(${h}, 55%, 55%)`
})
</script>

<template>
  <span
    class="inline-flex items-center justify-center rounded-full text-white font-semibold"
    :style="{ width: size + 'px', height: size + 'px', background: bg, fontSize: size * 0.45 + 'px' }"
    :title="name"
  >
    {{ initial }}
  </span>
</template>
