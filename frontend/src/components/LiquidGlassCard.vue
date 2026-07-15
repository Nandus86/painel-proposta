<template>
  <div ref="wrapperRef" class="liquid-glass-wrapper" :style="wrapperStyle">
    <div ref="glassRef" class="liquid-glass-target" :data-liquid-ignore="ignore ? '' : null">
      <div class="liquid-glass-content">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'

const props = defineProps({
  snapshot: { type: String, default: 'body' },
  resolution: { type: Number, default: 1.5 },
  frost: { type: Number, default: 2 },
  bevelDepth: { type: Number, default: 0.08 },
  bevelWidth: { type: Number, default: 0.15 },
  refraction: { type: Number, default: 0 },
  shadow: { type: Boolean, default: true },
  specular: { type: Boolean, default: true },
  tilt: { type: Boolean, default: false },
  magnify: { type: Number, default: 1 },
  width: { type: [String, Number], default: 'auto' },
  height: { type: [String, Number], default: 'auto' },
  borderRadius: { type: String, default: '12px' },
  ignore: { type: Boolean, default: false }
})

const wrapperRef = ref(null)
const glassRef = ref(null)
let glassInstance = null

const wrapperStyle = ref({
  width: typeof props.width === 'number' ? `${props.width}px` : props.width,
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  borderRadius: props.borderRadius
})

async function initLiquidGL() {
  if (!glassRef.value) return

  try {
    const { default: liquidGL } = await import('liquid-gl')
    await nextTick()

    glassInstance = liquidGL({
      snapshot: props.snapshot,
      target: glassRef.value,
      resolution: props.resolution,
      refraction: props.refraction,
      bevelDepth: props.bevelDepth,
      bevelWidth: props.bevelWidth,
      frost: props.frost,
      shadow: props.shadow,
      specular: props.specular,
      tilt: props.tilt,
      magnify: props.magnify,
      reveal: 'fade'
    })
    console.log('[LiquidGlassCard] initialized')
  } catch (err) {
    console.warn('[LiquidGlassCard] failed to init, using CSS fallback:', err)
    glassRef.value.classList.add('liquid-glass-fallback')
  }
}

function destroyLiquidGL() {
  if (glassInstance) {
    try {
      if (typeof glassInstance.destroy === 'function') {
        glassInstance.destroy()
      }
    } catch (e) {
      console.warn('[LiquidGlassCard] cleanup error:', e)
    }
    glassInstance = null
  }
}

onMounted(() => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (prefersReducedMotion) {
    glassRef.value?.classList.add('liquid-glass-fallback')
  } else {
    initLiquidGL()
  }
})

onBeforeUnmount(() => {
  destroyLiquidGL()
})
</script>

<style scoped>
.liquid-glass-wrapper {
  position: relative;
  overflow: hidden;
}

.liquid-glass-target {
  position: relative;
  width: 100%;
  height: 100%;
}

.liquid-glass-content {
  position: relative;
  z-index: 3;
  width: 100%;
  height: 100%;
}

.liquid-glass-fallback {
  background: var(--glass-bg, rgba(255, 255, 255, 0.85));
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border, rgba(228, 228, 231, 0.6));
  border-radius: inherit;
  box-shadow: var(--glass-shadow, 0 8px 32px rgba(0, 0, 0, 0.05));
}
</style>
