<script setup>
defineProps({ percent: { type: Number, default: 0 } })
</script>

<template>
  <div class="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
    <div
      class="h-full rounded-full bg-indigo-500 transition-all duration-500"
      :style="{ width: Math.min(100, Math.max(0, percent)) + '%' }"
    />
  </div>
</template>
