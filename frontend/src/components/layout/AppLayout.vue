<template>
  <div class="app-layout">
    <div class="sidebar-backdrop" :class="{ active: !sidebarCollapsed }" @click="sidebarCollapsed = true"></div>
    <AppSidebar :collapsed="sidebarCollapsed" @toggle="sidebarCollapsed = !sidebarCollapsed" />
    <div class="app-main" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <AppTopbar :collapsed="sidebarCollapsed" @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed" />
      <main class="app-content">
        <router-view v-slot="{ Component, route }">
          <transition name="page" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'

const sidebarCollapsed = ref(window.innerWidth <= 768)

function handleResize() {
  if (window.innerWidth <= 768) {
    sidebarCollapsed.value = true
  } else {
    sidebarCollapsed.value = false
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar-backdrop {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 99;
  backdrop-filter: blur(2px);
}

.app-main {
  flex: 1;
  margin-left: var(--sidebar-width);
  transition: margin-left var(--transition-normal);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-main.sidebar-collapsed {
  margin-left: var(--sidebar-collapsed-width);
}

.app-content {
  flex: 1;
  padding: 1.5rem 2rem;
  margin-top: var(--topbar-height);
  max-width: 1440px;
  width: 100%;
}

@media (max-width: 768px) {
  .sidebar-backdrop.active {
    display: block;
  }
  .app-main, .app-main.sidebar-collapsed {
    margin-left: 0;
  }
  .app-content {
    padding: 1rem;
  }
}
</style>
