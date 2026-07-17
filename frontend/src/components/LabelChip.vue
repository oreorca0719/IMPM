<script setup>
defineProps({
  label: { type: Object, required: true }, // { name, color }
  removable: { type: Boolean, default: false },
})
defineEmits(['remove'])
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium text-white"
    :style="{ background: label.color }"
  >
    {{ label.name }}
    <button
      v-if="removable"
      type="button"
      class="leading-none opacity-80 hover:opacity-100"
      @click.stop="$emit('remove')"
    >
      ×
    </button>
  </span>
</template>
