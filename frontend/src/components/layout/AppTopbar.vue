<template>
  <header class="topbar glass" :class="{ 'collapsed': collapsed }">
    <div class="topbar-left">
      <button class="mobile-toggle" @click="$emit('toggleSidebar')">
        <i class="pi pi-bars"></i>
      </button>
      <div class="page-title">
        <h1>{{ pageTitle }}</h1>
      </div>
    </div>

    <div class="topbar-right">
      <button class="theme-toggle-btn" @click="handleThemeToggle" :title="isDark ? 'Mudar para Tema Claro' : 'Mudar para Tema Escuro'">
        <i :class="isDark ? 'pi pi-moon' : 'pi pi-sun'"></i>
      </button>
      <span class="topbar-divider">|</span>
      <div class="welcome-user">
        Bem-vindo, {{ authStore.user?.nome || 'Usuário' }}
      </div>
      <span class="topbar-divider">|</span>
      <button class="logout-btn" @click="handleLogout">
        <i class="pi pi-sign-out"></i>
        <span>Sair</span>
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { isDarkMode, toggleDarkTheme } from '../../utils/theme'

const props = defineProps({
  collapsed: Boolean,
})

defineEmits(['toggleSidebar'])

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const showUserMenu = ref(false)
const isDark = ref(isDarkMode())

function handleThemeToggle() {
  isDark.value = toggleDarkTheme()
}

const pageTitle = computed(() => {
  const titles = {
    Dashboard: 'Dashboard',
    Empresa: 'Minha Empresa',
    Usuarios: 'Usuários',
    Clientes: 'Clientes',
  }
  return titles[route.name] || 'Painel'
})

const userInitials = computed(() => {
  const name = authStore.user?.nome || ''
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase()
})

const roleLabel = computed(() => {
  const labels = { admin: 'Administrador', gerente: 'Gerente', vendedor: 'Vendedor' }
  return labels[authStore.user?.role] || ''
})

function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value
}

function handleClickOutside(e) {
  showUserMenu.value = false
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.topbar {
  position: fixed;
  top: 0;
  right: 0;
  left: var(--sidebar-width);
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  z-index: 90;
  border: none !important;
  border-bottom: 1px solid var(--border-color) !important;
  border-radius: 0 !important;
  transition: left var(--transition-normal);
}

.topbar.collapsed {
  left: var(--sidebar-collapsed-width);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.mobile-toggle {
  display: none;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.2rem;
  cursor: pointer;
}

.page-title h1 {
  font-size: 1.125rem;
  font-weight: 590; /* Linear strong weight */
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
}

.theme-toggle-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  transition: all var(--transition-fast);
}

.theme-toggle-btn:hover {
  background: var(--surface-100);
  color: var(--primary-500);
}

html.dark .theme-toggle-btn:hover {
  background: var(--surface-800);
}

.empresa-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.empresa-badge i {
  font-size: 0.75rem;
  color: var(--primary-400);
}

.welcome-user {
  font-size: 0.85rem;
  font-weight: 510; /* Linear UI weight */
  color: var(--text-secondary);
}

.topbar-divider {
  color: var(--border-color);
  margin: 0 0.25rem;
}

.logout-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 510;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.logout-btn:hover {
  color: var(--text-primary);
}

.logout-btn i {
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .topbar {
    left: 0;
  }
  .mobile-toggle {
    display: block;
  }
  .empresa-badge {
    display: none;
  }
  .user-info {
    display: none;
  }
}
</style>
