<script setup lang="ts">
import { ref } from 'vue'
import DeviceCard from './DeviceCard.vue'

defineProps<{ group: any }>()
const emit = defineEmits(['refresh', 'editDevice'])
const collapsed = ref(false)
</script>

<template>
  <div class="device-group">
    <div class="group-header" @click="collapsed = !collapsed">
      <div class="group-left">
        <svg class="group-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8e8e93" stroke-width="2" stroke-linecap="round">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="group-name">{{ group.name }}</span>
        <span class="group-count">{{ group.devices?.length || 0 }}</span>
      </div>
      <svg class="chevron" :class="{ collapsed }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#c7c7cc" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </div>
    <Transition name="slide">
      <div v-show="!collapsed" class="group-devices">
        <DeviceCard
          v-for="device in group.devices"
          :key="device.id"
          :device="device"
          @refresh="emit('refresh')"
          @edit="(d) => emit('editDevice', d)"
        />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.device-group {
  margin-bottom: 8px;
}
.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 4px;
  cursor: pointer;
  user-select: none;
}
.group-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.group-icon { opacity: 0.5; }
.group-name {
  font-size: 14px;
  font-weight: 600;
  color: #3a3a3c;
  letter-spacing: -0.2px;
}
.group-count {
  font-size: 12px;
  font-weight: 600;
  color: #8e8e93;
  background: rgba(142,142,147,0.12);
  padding: 1px 8px;
  border-radius: 20px;
}
.chevron {
  transition: transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.chevron.collapsed {
  transform: rotate(-90deg);
}
.group-devices {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 12px;
  padding-bottom: 12px;
}
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
