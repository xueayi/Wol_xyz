<script setup lang="ts">
defineProps<{ show: boolean; title: string; content: string }>()
const emit = defineEmits(['update:show'])
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    :title="title" style="width: 600px" :bordered="false">
    <div v-html="content" style="line-height: 1.8; font-size: 14px; color: #555;"></div>
  </n-modal>
</template>
