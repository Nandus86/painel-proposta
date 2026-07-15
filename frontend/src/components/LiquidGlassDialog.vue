<template>
  <Dialog v-bind="$attrs" :modal="modal" :visible="dialogVisible" :style="dialogStyle" @update:visible="onVisibleChange">
    <template #container="{ onClose }">
      <LiquidGlassCard
        class="liquid-dialog-card"
        :frost="2"
        :bevelDepth="0.06"
        :bevelWidth="0.12"
        :shadow="true"
        :specular="true"
        :borderRadius="borderRadius"
        :height="'auto'"
      >
        <div class="liquid-dialog-inner" :style="{ borderRadius: borderRadius, minWidth: minWidth }">
          <slot name="content" :onClose="onClose" />
        </div>
      </LiquidGlassCard>
    </template>
  </Dialog>
</template>

<script setup>
import Dialog from 'primevue/dialog'
import LiquidGlassCard from './LiquidGlassCard.vue'
import { computed } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  modal: { type: Boolean, default: true },
  width: { type: String, default: '500px' },
  minWidth: { type: String, default: '350px' },
  borderRadius: { type: String, default: '16px' }
})

const emit = defineEmits(['update:visible'])

const dialogVisible = computed(() => props.visible)

const dialogStyle = computed(() => ({
  width: props.width,
  minWidth: props.minWidth,
  background: 'transparent',
  border: 'none',
  boxShadow: 'none'
}))

function onVisibleChange(val) {
  emit('update:visible', val)
}
</script>

<style scoped>
.liquid-dialog-card {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1001;
}

.liquid-dialog-inner {
  padding: 1.5rem;
  background: transparent;
  min-height: 100px;
}

:deep(.p-dialog) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

:deep(.p-dialog .p-dialog-header) {
  display: none;
}

:deep(.p-dialog .p-dialog-content) {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}

:deep(.p-dialog-mask) {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
}
</style>
