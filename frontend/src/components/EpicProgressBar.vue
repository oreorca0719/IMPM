<script setup>
defineProps({ percent: { type: Number, default: 0 } })
</script>

<template>
  <div class="h-2 w-full rounded-full bg-slate-200 overflow-hidden">
    <div
      class="h-full rounded-full bg-brand-500 transition-all"
      :style="{ width: Math.min(100, Math.max(0, percent)) + '%' }"
    />
  </div>
</template>
