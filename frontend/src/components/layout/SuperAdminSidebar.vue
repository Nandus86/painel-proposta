<template>
  <aside class="sidebar" :class="{ collapsed }">
    <!-- Logo -->
    <div class="sidebar-header">
      <div class="logo" @click="$router.push('/admin')">
        <div class="logo-icon admin-icon">
          <i class="pi pi-globe"></i>
        </div>
        <transition name="fade-text">
          <div v-if="!collapsed" class="logo-text">
            <span class="logo-title">Dekto</span>
            <span class="logo-subtitle">SUPER ADMIN</span>
          </div>
        </transition>
      </div>
      <button class="toggle-btn" @click="$emit('toggle')">
        <i :class="collapsed ? 'pi pi-angle-right' : 'pi pi-angle-left'"></i>
      </button>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <div class="nav-section">
        <span v-if="!collapsed" class="nav-label">SISTEMA</span>
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <i :class="item.icon"></i>
          <transition name="fade-text">
            <span v-if="!collapsed" class="nav-text">{{ item.label }}</span>
          </transition>
        </router-link>
      </div>
      
      <!-- Back to Normal App -->
      <div class="nav-section mt-4">
        <router-link to="/" class="nav-item nav-item-back">
          <i class="pi pi-arrow-left"></i>
          <transition name="fade-text">
            <span v-if="!collapsed" class="nav-text">Voltar ao App</span>
          </transition>
        </router-link>
      </div>
    </nav>

    <!-- Footer -->
    <div class="sidebar-footer">
      <div v-if="!collapsed" class="version-badge">v1.0.0</div>
    </div>
  </aside>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const props = defineProps({
  collapsed: Boolean,
})

defineEmits(['toggle'])

const route = useRoute()

const navItems = computed(() => {
  return [
    { path: '/admin', icon: 'pi pi-chart-bar', label: 'Dashboard' },
    { path: '/admin/empresas', icon: 'pi pi-building', label: 'Gestão de Empresas' },
    { path: '/admin/configuracoes', icon: 'pi pi-cog', label: 'Configurações Globais' },
  ]
})

function isActive(path) {
  return route.path.startsWith(path)
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width var(--transition-normal);
  overflow: hidden;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 0.75rem;
  border-bottom: 1px solid var(--border-color);
  min-height: var(--topbar-height);
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.logo-icon.admin-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--border-radius-sm);
  background: linear-gradient(135deg, #1e293b, #0f172a); /* Dark theme for admin */
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}

.logo-icon i {
  font-size: 0.95rem;
  color: white;
}

.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.logo-title {
  font-weight: 700;
  font-size: 1.3rem;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.logo-subtitle {
  font-size: 0.55rem;
  color: #ef4444; /* Red color for super admin */
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
}

.toggle-btn {
  width: 28px;
  height: 28px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.toggle-btn:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  padding: 1rem 0.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-section {
  margin-bottom: 1.25rem;
}

.nav-label {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 1.5px;
  padding: 0 0.75rem;
  margin-bottom: 0.5rem;
  display: block;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.75rem;
  border-radius: var(--border-radius-sm);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  text-decoration: none;
  white-space: nowrap;
  position: relative;
}

.nav-item:hover {
  background: rgba(239, 68, 68, 0.08); /* Red hover */
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(239, 68, 68, 0.12); /* Red active */
  color: #ef4444;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 50%;
  background: #ef4444;
  border-radius: 0 2px 2px 0;
}

.nav-item i {
  font-size: 1rem;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.nav-item-back {
  color: var(--text-muted);
}
.nav-item-back:hover {
  background: var(--surface-100);
  color: var(--text-primary);
}

.nav-text {
  font-size: 0.875rem;
  font-weight: 500;
}

/* Footer */
.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: center;
}

.version-badge {
  font-size: 0.7rem;
  color: var(--text-muted);
  background: var(--bg-card);
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
}

/* Transitions */
.fade-text-enter-active,
.fade-text-leave-active {
  transition: opacity 0.15s ease;
}
.fade-text-enter-from,
.fade-text-leave-to {
  opacity: 0;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0.65rem;
}

.sidebar.collapsed .nav-label {
  display: none;
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 1rem 0.5rem;
}

.sidebar.collapsed .toggle-btn {
  display: none;
}

.sidebar.collapsed .nav-item.active::before {
  left: 0;
}
</style>
