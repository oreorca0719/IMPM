<script setup>
defineProps({
  label: { type: Object, required: true }, // { name, color }
  removable: { type: Boolean, default: false },
})
defineEmits(['remove'])
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium"
    :style="{ color: label.color, background: label.color + '1a' }"
  >
    <span class="h-1.5 w-1.5 rounded-full" :style="{ background: label.color }" />
    {{ label.name }}
    <button
      v-if="removable"
      type="button"
      class="ml-0.5 leading-none opacity-60 hover:opacity-100"
      @click.stop="$emit('remove')"
    >
      ×
    </button>
  </span>
</template>
