<template>
  <aside class="sidebar" :class="{ collapsed }">
    <!-- Logo -->
    <div class="sidebar-header">
      <div class="logo" @click="$router.push('/')">
        <div class="logo-icon">
          <i class="pi pi-bolt"></i>
        </div>
        <transition name="fade-text">
          <div v-if="!collapsed" class="logo-text">
            <span class="logo-title">Dekto</span>
            <span class="logo-subtitle">PROPOSTAS</span>
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
    </nav>

    <!-- Footer -->
    <div class="sidebar-footer">
      <div v-if="!collapsed" class="version-badge">v1.0.0</div>
    </div>
  </aside>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { computed } from 'vue'

const props = defineProps({
  collapsed: Boolean,
})

defineEmits(['toggle'])

const route = useRoute()
const authStore = useAuthStore()

const navItems = computed(() => {
  const items = [
    { path: '/', icon: 'pi pi-th-large', label: 'Painel' },
    { path: '/orcamentos', icon: 'pi pi-calculator', label: 'Orçamentos' },
    { path: '/propostas', icon: 'pi pi-file', label: 'Propostas' },
    { path: '/clientes', icon: 'pi pi-users', label: 'Clientes' },
    { path: '/categorias', icon: 'pi pi-tags', label: 'Categorias' },
    { path: '/servicos', icon: 'pi pi-box', label: 'Produtos e Serviços' },
    { path: '/modelos', icon: 'pi pi-copy', label: 'Modelos de Proposta' },
    { path: '/integracoes', icon: 'pi pi-share-alt', label: 'Integrações' },
    { path: '/empresa', icon: 'pi pi-building', label: 'Dados da Empresa' },
    { path: '/configuracoes', icon: 'pi pi-cog', label: 'Configurações' },
  ]
  if (authStore.isSuperuser) {
    items.push({ path: '/admin/empresas', icon: 'pi pi-globe', label: 'Admin Global' })
  }
  return items
})

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path === path
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
  transition: transform var(--transition-normal), width var(--transition-normal);
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

.logo-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--border-radius-sm);
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-glow-primary);
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
  color: var(--text-muted);
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
  background: rgba(var(--primary-rgb), 0.08); /* Brand Peach-Yellow Hover */
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(var(--primary-rgb), 0.12); /* Brand Peach-Yellow Active */
  color: var(--primary-600);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 50%;
  background: var(--primary-600);
  border-radius: 0 2px 2px 0;
}

.nav-item i {
  font-size: 1rem;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
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
  flex-direction: column;
  gap: 1rem;
}

.sidebar.collapsed .nav-item.active::before {
  left: 0;
}

@media (max-width: 768px) {
  .sidebar {
    transform: translateX(0);
    width: var(--sidebar-width) !important;
  }
  .sidebar.collapsed {
    transform: translateX(-100%);
  }
  .sidebar.collapsed .sidebar-header {
    flex-direction: row;
    padding: 1rem 0.75rem;
    justify-content: space-between;
  }
}
</style>
