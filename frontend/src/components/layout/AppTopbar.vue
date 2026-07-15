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
      <div class="notification-bell" @click="notificationsStore.togglePanel()">
        <i class="pi pi-bell"></i>
        <span v-if="notificationsStore.unreadCount > 0" class="notification-badge">{{ notificationsStore.unreadCount }}</span>
      </div>
      <div v-if="notificationsStore.showPanel" class="notification-panel glass" @click.stop>
        <div class="notif-header">
          <span>Notificações</span>
          <button class="notif-clear" @click="notificationsStore.markAllRead()">Marcar todas lidas</button>
        </div>
        <div class="notif-list" v-if="notificationsStore.notifications.length > 0">
          <div
            v-for="n in notificationsStore.notifications"
            :key="n.id"
            class="notif-item"
            :class="{ unread: !n.read }"
            @click="notificationsStore.markRead(n.id)"
          >
            <div class="notif-title">{{ n.title }}</div>
            <div class="notif-msg">{{ n.message }}</div>
            <div class="notif-time">{{ formatTime(n.createdAt) }}</div>
          </div>
        </div>
        <div v-else class="notif-empty">Nenhuma notificação</div>
      </div>
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
import { useNotificationsStore } from '../../stores/notifications'
import { isDarkMode, toggleDarkTheme } from '../../utils/theme'

const props = defineProps({
  collapsed: Boolean,
})

defineEmits(['toggleSidebar'])

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()
const showUserMenu = ref(false)
const isDark = ref(isDarkMode())

function formatTime(dateStr) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return 'Agora'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}min atrás`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h atrás`
  return date.toLocaleDateString('pt-BR')
}

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

.notification-bell {
  position: relative;
  cursor: pointer;
  font-size: 1.1rem;
  color: var(--text-secondary);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all var(--transition-fast);
}

.notification-bell:hover {
  background: var(--surface-100);
  color: var(--primary-500);
}

.notification-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background: var(--accent-red);
  color: white;
  font-size: 0.6rem;
  font-weight: 700;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-panel {
  position: absolute;
  top: 100%;
  right: 0;
  width: 340px;
  max-height: 400px;
  overflow-y: auto;
  border-radius: var(--border-radius-lg);
  z-index: 200;
  margin-top: 0.5rem;
}

.notif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
  font-size: 0.9rem;
}

.notif-clear {
  background: none;
  border: none;
  color: var(--primary-400);
  font-size: 0.75rem;
  cursor: pointer;
}

.notif-list {
  padding: 0.25rem 0;
}

.notif-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  transition: background var(--transition-fast);
}

.notif-item:hover {
  background: var(--surface-100);
}

.notif-item.unread {
  background: rgba(var(--primary-rgb), 0.04);
}

.notif-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.notif-msg {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 0.15rem;
}

.notif-time {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.notif-empty {
  padding: 2rem;
  text-align: center;
  font-size: 0.85rem;
  color: var(--text-muted);
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
