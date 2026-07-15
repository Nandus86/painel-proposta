<template>
  <div class="app-layout">
    <SuperAdminSidebar :collapsed="sidebarCollapsed" @toggle="sidebarCollapsed = !sidebarCollapsed" />
    <div class="app-main" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <AppTopbar @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed" />
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
import { ref } from 'vue'
import SuperAdminSidebar from './SuperAdminSidebar.vue'
import AppTopbar from './AppTopbar.vue'

const sidebarCollapsed = ref(false)
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

.app-main {
  flex: 1;
  margin-left: var(--sidebar-width);
  transition: margin-left var(--transition-normal);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--surface-50); /* slightly different background for admin */
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
  .app-main {
    margin-left: 0;
  }
  .app-content {
    padding: 1rem;
  }
}
</style>
